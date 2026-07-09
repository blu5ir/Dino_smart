import json
import re
from database.db_manager import DatabaseManager

class QuizService:
    @staticmethod
    def get_workspace_context(db_manager: DatabaseManager, workspace_id: int) -> str:
        docs = db_manager.get_documents(workspace_id)
        if not docs:
            return ""
        return "\n\n=== DOCUMENT: " + "\n\n=== DOCUMENT: ".join([f"{d['name']} ===\n{d['content']}" for d in docs])

    @classmethod
    def generate_quiz(cls, provider, db_manager: DatabaseManager, workspace_id: int, difficulty: str, count: int, temperature: float = 0.7) -> list:
        """Generate a quiz with mixed question types based on materials."""
        context = cls.get_workspace_context(db_manager, workspace_id)
        if not context.strip():
            return []

        import random
        random_seed = random.randint(1, 1000000)

        system_instruction = "You are an expert exam developer. You output only valid JSON arrays."
        
        prompt = (
            f"Develop a quiz based on the following study materials.\n"
            f"Parameters:\n"
            f"- Difficulty Level: {difficulty}\n"
            f"- Question Count: {count}\n"
            f"- Randomness Seed: {random_seed} (Choose a unique, fresh set of concepts and questions for this randomized variation)\n"
            f"- Allowed Question Types: 'mcq' (Multiple Choice), 'tf' (True/False), 'fill' (Fill in the Blank), "
            f"'short' (Short Answer), 'matching' (Matching pairs), 'numerical' (Numerical problems).\n\n"
            f"Create a diverse, balanced mix of these question types.\n"
            f"You MUST return ONLY a valid JSON array of objects. Do not include markdown code block styling. "
            f"Each question object in the array must contain these exact keys:\n"
            f"- 'type': String, one of ['mcq', 'tf', 'fill', 'short', 'matching', 'numerical']\n"
            f"- 'question': String, the question text. For 'matching', specify the left items to match (e.g. 'Match A, B, C to 1, 2, 3').\n"
            f"- 'options': For 'mcq', list 4 choices. For 'matching', list the right-hand items to select from. For other types, output [].\n"
            f"- 'answer': For 'mcq', the exact string match. For 'tf', 'True' or 'False'. For 'fill' or 'short', the correct response. "
            f"For 'matching', a key-value dictionary mapping the items (e.g., {{'A': '1', 'B': '2'}}). For 'numerical', a string representing the number.\n"
            f"- 'explanation': String, explaining the concept and why the answer is correct.\n"
            f"- 'topic': String, the specific topic/sub-topic tested.\n\n"
            f"Study Materials:\n{context[:15000]}"
        )

        raw_out = provider.generate_text(prompt, system_instruction=system_instruction, temperature=temperature)
        
        # Clean outputs
        cleaned = raw_out.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```(?:json)?\n', '', cleaned)
            cleaned = re.sub(r'\n```$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            questions = json.loads(cleaned)
            if isinstance(questions, list):
                # Ensure they have id
                for i, q in enumerate(questions):
                    q["id"] = i + 1
                    if q.get("type") == "mcq" and "options" in q:
                        random.shuffle(q["options"])
                db_manager.save_quiz(workspace_id, difficulty, questions)
                return questions
        except Exception as e:
            # Try to regex parse if json loading failed
            try:
                # Basic bracket extract
                match = re.search(r'\[\s*\{.*\}\s*\]', cleaned, re.DOTALL)
                if match:
                    questions = json.loads(match.group(0))
                    for i, q in enumerate(questions):
                        q["id"] = i + 1
                        if q.get("type") == "mcq" and "options" in q:
                            random.shuffle(q["options"])
                    db_manager.save_quiz(workspace_id, difficulty, questions)
                    return questions
            except Exception:
                pass
                
        # Generate generic fallback questions if parser fails
        fallback_questions = [
            {
                "id": 1,
                "type": "tf",
                "question": "The uploaded materials outline important academic concepts.",
                "options": [],
                "answer": "True",
                "explanation": "This is a placeholder question because the AI output could not be parsed.",
                "topic": "General Ingestion"
            }
        ]
        db_manager.save_quiz(workspace_id, difficulty, fallback_questions)
        return fallback_questions

    @classmethod
    def evaluate_quiz(cls, questions: list, user_responses: dict) -> dict:
        """
        Evaluates user answers.
        user_responses is a dict: {question_id: user_input}
        Returns a grading summary: {score, total, accuracy, details: {q_id: {correct, user_ans, correct_ans}}, topic_analysis}
        """
        score = 0
        total = len(questions)
        details = {}
        topic_analysis = {} # topic: {"correct": X, "total": Y}

        for q in questions:
            q_id = q["id"]
            q_type = q["type"]
            correct_ans = q["answer"]
            user_ans = user_responses.get(q_id, "")
            
            topic = q.get("topic", "General")
            if topic not in topic_analysis:
                topic_analysis[topic] = {"correct": 0, "total": 0}
            topic_analysis[topic]["total"] += 1

            is_correct = False

            if q_type == "mcq":
                is_correct = str(user_ans).strip().lower() == str(correct_ans).strip().lower()
            elif q_type == "tf":
                is_correct = str(user_ans).strip().lower() == str(correct_ans).strip().lower()
            elif q_type == "matching":
                # For matching, user_ans should be a dict: {left: right}
                # correct_ans is a dict
                if isinstance(user_ans, dict) and isinstance(correct_ans, dict):
                    # Check how many matched correctly
                    matches = 0
                    for k, v in correct_ans.items():
                        if str(user_ans.get(k)).strip().lower() == str(v).strip().lower():
                            matches += 1
                    is_correct = matches == len(correct_ans)
                    # Modify score as fractional? Let's keep it simple: all or nothing, or fractional
                    # Let's say it's correct if all matches are correct
                else:
                    is_correct = str(user_ans).strip().lower() == str(correct_ans).strip().lower()
            elif q_type in ["fill", "short", "numerical"]:
                # Soft match: strip, lower case, check equality
                clean_user = str(user_ans).strip().lower()
                clean_correct = str(correct_ans).strip().lower()
                # If numeric, convert to float and compare
                try:
                    is_correct = float(clean_user) == float(clean_correct)
                except ValueError:
                    is_correct = clean_user == clean_correct or clean_correct in clean_user

            if is_correct:
                score += 1
                topic_analysis[topic]["correct"] += 1

            details[q_id] = {
                "correct": is_correct,
                "user_answer": user_ans,
                "correct_answer": correct_ans,
                "explanation": q.get("explanation", "")
            }

        accuracy = (score / total) * 100 if total > 0 else 0
        return {
            "score": score,
            "total": total,
            "accuracy": accuracy,
            "details": details,
            "topic_analysis": topic_analysis
        }
