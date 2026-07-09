from database.db_manager import DatabaseManager

class RevisionService:
    REVISION_PROMPTS = {
        "cheat_sheet": (
            "Generate a highly concentrated Cheat Sheet based on the provided study materials. "
            "Include key concepts, tables, rules, and brief examples. Use a dual-column markdown layout if possible. "
            "Make it visually structured and easy to scan."
        ),
        "formula_sheet": (
            "Extract and compile a Formula Sheet from the provided study materials. "
            "List all mathematical formulas, physical equations, chemical reactions, algorithms, or structural laws. "
            "For each formula, define all variables and provide a brief worked snippet. "
            "If no formulas exist, compile the core rules and principles."
        ),
        "last_minute": (
            "Create a high-yield 'Last Minute Notes' sheet. "
            "Identify the most critical, high-probability topics likely to appear on an exam. "
            "Use bullet points, bold key terms, and summarize each concept in a single sentence. "
            "Highlight common exam trick questions."
        ),
        "five_min": (
            "Provide a '5-Minute Revision Guide' for these materials. "
            "Summarize the content in exactly 5 key sections: "
            "1. Core Goal, 2. Essential Terminology, 3. The 3 Big Ideas, 4. Critical Rules to Remember, 5. Ultimate Takeaways. "
            "Keep it highly readable, clear, and direct."
        ),
        "definitions": (
            "Generate a comprehensive list of 'Important Definitions' or a Glossary from the study materials. "
            "List key terms alphabetically, followed by their precise definition as found in or inferred from the text."
        ),
        "checklist": (
            "Create an 'Exam Checklist'. "
            "Develop an active recall checklist of questions, topics, and problem-types the student MUST master before taking their exam. "
            "Format them as a checklist: - [ ] Topic/Question. Include brief hints for each checklist item."
        )
    }

    @classmethod
    def generate_revision_material(cls, provider, db_manager: DatabaseManager, workspace_id: int, material_type: str) -> str:
        """Generate specialized revision material from workspace documents."""
        docs = db_manager.get_documents(workspace_id)
        if not docs:
            return "No study materials available. Please upload files in the workspace."

        context_parts = []
        for d in docs:
            context_parts.append(f"--- DOCUMENT: {d['name']} ---\n{d['content']}")
        context = "\n\n".join(context_parts)

        sub_prompt = cls.REVISION_PROMPTS.get(material_type)
        if not sub_prompt:
            return "Unknown revision material type."

        system_instruction = "You are an expert revision tutor who structures information beautifully."
        
        prompt = (
            f"{sub_prompt}\n\n"
            "Ensure everything is strictly grounded in the materials provided. Do not invent details. "
            "Use rich markdown tables, bold highlights, code segments, or bullet lists to make it look highly professional.\n\n"
            f"Study Materials:\n{context[:15000]}"
        )

        return provider.generate_text(prompt, system_instruction=system_instruction)
