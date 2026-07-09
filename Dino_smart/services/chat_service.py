from database.db_manager import DatabaseManager

class ChatService:
    MODE_DIRECTIVES = {
        "regular": "Provide a clear, detailed, and directly grounded answer based on the materials.",
        "eli10": "Explain like I'm 10. Use simple analogies, elementary vocabulary, and avoid complex terminology or jargon.",
        "professor": "Explain like a professor. Provide an academically rigorous explanation with precise vocabulary, theoretical depth, and formal structure.",
        "hints": "Give hints only. Do NOT reveal the direct answer. Provide guiding questions or conceptual clues to help the student find the answer on their own.",
        "step_by_step": "Provide a detailed step-by-step solution. Break down the logic or math into clear, numbered, sequential stages.",
        "examples": "Provide concrete, real-world examples that illustrate the concepts in the material.",
        "simplify": "Simplify the concepts. Condense the information into bullet points, highlighting only the core definitions and relationships."
    }

    @classmethod
    def get_grounded_response(cls, provider, db_manager: DatabaseManager, workspace_id: int, question: str, mode: str = "regular", chat_history: list = None) -> str:
        """
        Retrieves the workspace documents, prepends them as context,
        and prompts the LLM using a strict grounding system instruction.
        """
        # Get workspace documents
        docs = db_manager.get_documents(workspace_id)
        if not docs:
            return "No study materials have been uploaded to this workspace yet. Please upload files under the 'Add Study Material' tab first."

        # Compile documents text
        context_parts = []
        for d in docs:
            context_parts.append(f"--- DOCUMENT: {d['name']} ---\n{d['content']}")
        context = "\n\n".join(context_parts)
        
        directive = cls.MODE_DIRECTIVES.get(mode, cls.MODE_DIRECTIVES["regular"])

        system_instruction = (
            "You are Dino Smart, a strict, highly grounded AI study assistant. "
            "You are helping a student review their course materials. You must adhere to the following rules:\n"
            "1. You must answer questions using ONLY the provided Study Material.\n"
            "2. If the answer cannot be found in the provided Study Material, you must state exactly: "
            "'I cannot find this information in the uploaded study materials. Please upload relevant files containing this topic.' "
            "Do not make up any facts.\n"
            "3. Do not reference outside knowledge or websites unless the user explicitly requests outside knowledge in their prompt.\n"
            f"4. Format Directive: {directive}\n"
        )
        
        # Build chat context history if available
        prompt_parts = []
        prompt_parts.append("--- BEGIN STUDY MATERIAL ---")
        prompt_parts.append(context[:25000]) # Cap text context to avoid token overflow in small local models
        prompt_parts.append("--- END STUDY MATERIAL ---\n")
        
        if chat_history:
            prompt_parts.append("Recent Chat History:")
            for msg in chat_history[-6:]: # Include last 3 exchanges
                role = "Student" if msg["role"] == "user" else "Tutor"
                prompt_parts.append(f"{role}: {msg['content']}")
                
        prompt_parts.append(f"Student: {question}")
        prompt_parts.append("Tutor:")
        
        prompt = "\n".join(prompt_parts)
        
        return provider.generate_text(prompt, system_instruction=system_instruction)
