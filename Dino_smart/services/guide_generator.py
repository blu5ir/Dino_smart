import json
import re
import concurrent.futures
from database.db_manager import DatabaseManager

class GuideGenerator:
    @staticmethod
    def get_workspace_context(db_manager: DatabaseManager, workspace_id: int) -> str:
        """Combine all documents in the workspace into a single context string."""
        docs = db_manager.get_documents(workspace_id)
        if not docs:
            return ""
        return "\n\n=== DOCUMENT: " + "\n\n=== DOCUMENT: ".join([f"{d['name']} ===\n{d['content']}" for d in docs])

    @classmethod
    def generate_topics_outline(cls, provider, context: str, mode: str) -> list:
        """Stage 1: Generate a high-level list of topics from materials."""
        num_topics = 6 if mode == "deep_dive" else 8
        
        system_instruction = "You are a professional academic curriculum designer. You output only valid JSON."
        prompt = (
            f"Based on the following study materials, identify the top {num_topics} core topics/concepts that a student must learn. "
            "Return only a valid JSON array of strings containing the topic titles. "
            "Do not include markdown tags like ```json or any other text. Just return the JSON list.\n\n"
            f"Example output:\n[\"Topic A\", \"Topic B\", \"Topic C\"]\n\n"
            f"Study Materials:\n{context[:15000]}"
        )
        
        raw_out = provider.generate_text(prompt, system_instruction=system_instruction)
        
        # Parse output
        try:
            # Clean possible markdown block markers
            cleaned = raw_out.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:json)?\n', '', cleaned)
                cleaned = re.sub(r'\n```$', '', cleaned)
            cleaned = cleaned.strip()
            
            topics = json.loads(cleaned)
            if isinstance(topics, list):
                return [str(t) for t in topics][:num_topics]
        except Exception:
            # Fallback parsing in case JSON output was messy
            import re
            found = re.findall(r'"([^"]+)"', raw_out)
            if len(found) >= 3:
                return found[:num_topics]
                
        # Default fallback if LLM failed
        return [f"Core Concept {i+1}" for i in range(num_topics)]

    @classmethod
    def generate_single_topic(cls, provider, context: str, topic: str, mode: str) -> str:
        """Stage 2: Generate content for a single topic."""
        system_instruction = "You are an expert university professor and private tutor."
        
        if mode == "deep_dive":
            prompt = (
                f"Generate a highly detailed 'Deep Dive' guide section for the topic '{topic}' based on the provided study materials. "
                "You must strictly use the following exact sections with H3 headings: "
                "### Concept, ### Why it matters, ### Key Rules, ### Common Mistakes, ### Memory Tricks, ### Worked Example, ### Practice Challenge, ### Hidden Answer, ### Exam Tips.\n\n"
                "In the '### Hidden Answer' section, you MUST format the answer inside a collapsible HTML details element, like so:\n"
                "<details>\n  <summary>Reveal Answer & Explanation</summary>\n  [Detailed step-by-step solution here]\n</details>\n\n"
                "Guidelines:\n"
                "1. If relevant, include flowcharts, timelines, comparison tables, formulas, or mind maps using Markdown tables or Mermaid.js code blocks.\n"
                "2. Rely strictly on the provided materials. If the materials are sparse, supplement them with standard educational facts but clearly state what is from the material.\n"
                "3. Do not include introductory greetings or concluding remarks. Start immediately with '### Concept'.\n\n"
                f"Study Materials:\n{context[:12000]}"
            )
        else:  # Cram mode
            prompt = (
                f"Generate a concise, high-impact 'Cram' guide section for the topic '{topic}' based on the provided study materials. "
                "You must output exactly these five bullet points:\n"
                "- **Rule**: [Short summary of rule/principle]\n"
                "- **Formula**: [Core formula if any, or primary definition]\n"
                "- **Mini Example**: [A very brief practical illustration]\n"
                "- **Challenge**: [A quick, direct exam question]\n"
                "- **Answer**: [The correct answer in brackets, e.g. (Answer: X)]\n\n"
                "CRITICAL Word Limit: The entire output MUST NOT exceed 60 words in total. Keep it extremely brief and dense. Do not include introductory text.\n\n"
                f"Study Materials:\n{context[:12000]}"
            )
            
        return provider.generate_text(prompt, system_instruction=system_instruction)

    @classmethod
    def generate_full_guide(cls, provider, db_manager: DatabaseManager, workspace_id: int, mode: str, progress_bar_callback=None) -> dict:
        """
        Coordinates the dual-stage Skeleton-of-Thought generation.
        Stage 1: Outline extraction.
        Stage 2: Section generation (parallelized via threads).
        Stores in DB and returns the guide object.
        """
        context = cls.get_workspace_context(db_manager, workspace_id)
        if not context.strip():
            return {"topics": [], "content": {}}
            
        # Stage 1: Get topics
        if progress_bar_callback:
            progress_bar_callback(10, "Extracting major topics outline...")
            
        topics = cls.generate_topics_outline(provider, context, mode)
        
        # Stage 2: Generate sections
        content_dict = {}
        total_topics = len(topics)
        
        # Run parallel generation with ThreadPoolExecutor
        if progress_bar_callback:
            progress_bar_callback(30, f"Generating {total_topics} topics in parallel...")
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Map topics to worker futures
            future_to_topic = {
                executor.submit(cls.generate_single_topic, provider, context, topic, mode): topic 
                for topic in topics
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_topic):
                topic = future_to_topic[future]
                try:
                    section_content = future.result()
                    content_dict[topic] = section_content
                except Exception as e:
                    content_dict[topic] = f"Error generating topic content: {str(e)}"
                
                completed += 1
                if progress_bar_callback:
                    pct = 30 + int((completed / total_topics) * 60)
                    progress_bar_callback(pct, f"Completed topic {completed}/{total_topics}: {topic}")

        if progress_bar_callback:
            progress_bar_callback(95, "Saving generated guide to database...")
            
        # Save in database
        db_manager.save_study_guide(workspace_id, mode, topics, content_dict)
        
        if progress_bar_callback:
            progress_bar_callback(100, "Guide generation complete!")
            
        return {
            "workspace_id": workspace_id,
            "mode": mode,
            "topics": topics,
            "content": content_dict
        }

    @classmethod
    def regenerate_topic(cls, provider, db_manager: DatabaseManager, workspace_id: int, topic: str) -> dict:
        """Regenerate a single topic section and update the database record."""
        guide = db_manager.get_study_guide(workspace_id)
        if not guide:
            return None
            
        context = cls.get_workspace_context(db_manager, workspace_id)
        new_content = cls.generate_single_topic(provider, context, topic, guide["mode"])
        
        # Update content JSON
        guide["content"][topic] = new_content
        db_manager.save_study_guide(
            workspace_id=workspace_id,
            mode=guide["mode"],
            topics=guide["topics"],
            content_dict=guide["content"]
        )
        
        return guide
