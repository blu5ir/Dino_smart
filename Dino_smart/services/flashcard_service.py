import json
import re
from database.db_manager import DatabaseManager

class FlashcardService:
    @staticmethod
    def get_workspace_context(db_manager: DatabaseManager, workspace_id: int) -> str:
        docs = db_manager.get_documents(workspace_id)
        if not docs:
            return ""
        return "\n\n=== DOCUMENT: " + "\n\n=== DOCUMENT: ".join([f"{d['name']} ===\n{d['content']}" for d in docs])

    @classmethod
    def generate_flashcards(cls, provider, db_manager: DatabaseManager, workspace_id: int) -> list:
        """Generate flashcards from study materials."""
        context = cls.get_workspace_context(db_manager, workspace_id)
        if not context.strip():
            return []

        import random
        random_seed = random.randint(1, 1000000)
        
        system_instruction = "You are an expert tutor. You output only valid JSON lists."
        prompt = (
            f"Generate 8 to 12 flashcards to test key concepts from the following materials.\n"
            f"Randomness Seed: {random_seed} (Ensure a unique, fresh selection of concepts).\n"
            "Each card must have a clear question or cue on the 'front', and a concise answer or explanation on the 'back'.\n"
            "Keep card content clear, focused, and easy to memorize.\n\n"
            "You MUST return ONLY a valid JSON array of objects. Do not write any introduction or code formatting blocks. "
            "Each object must have these exact keys:\n"
            "- 'front': String, the question or prompt.\n"
            "- 'back': String, the answer.\n\n"
            f"Study Materials:\n{context[:15000]}"
        )

        raw_out = provider.generate_text(prompt, system_instruction=system_instruction)
        
        # Clean outputs
        cleaned = raw_out.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```(?:json)?\n', '', cleaned)
            cleaned = re.sub(r'\n```$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            cards = json.loads(cleaned)
            if isinstance(cards, list):
                db_manager.add_flashcards(workspace_id, cards)
                return cards
        except Exception:
            # Fallback parsing
            try:
                match = re.search(r'\[\s*\{.*\}\s*\]', cleaned, re.DOTALL)
                if match:
                    cards = json.loads(match.group(0))
                    db_manager.add_flashcards(workspace_id, cards)
                    return cards
            except Exception:
                pass
                
        # Generic fallbacks
        fallback = [
            {"front": "Key Term: What is the main topic of your notes?", "back": "Check the document overview."}
        ]
        db_manager.add_flashcards(workspace_id, fallback)
        return fallback
