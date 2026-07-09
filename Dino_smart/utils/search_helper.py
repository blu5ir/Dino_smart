import re
from database.db_manager import DatabaseManager

class SearchHelper:
    @staticmethod
    def clean_query(query: str) -> list:
        """Split query into lowercase alphanumeric keywords."""
        return [w.lower() for w in re.findall(r'\w+', query) if len(w) > 1]

    @classmethod
    def search_all(cls, db_manager: DatabaseManager, workspace_id: int, query: str) -> list:
        """
        Search across notes, documents, flashcards, guides, and quizzes.
        Returns a sorted list of matches: [{"source": "...", "title": "...", "content_snippet": "...", "score": X}]
        """
        keywords = cls.clean_query(query)
        if not keywords:
            return []

        results = []

        # 1. Search Documents
        docs = db_manager.get_documents(workspace_id)
        for doc in docs:
            score = 0
            doc_text = f"{doc['name']} {doc['content']} {doc['summary'] or ''}".lower()
            for kw in keywords:
                score += doc_text.count(kw)
            
            if score > 0:
                snippet = doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
                results.append({
                    "source": "Document Upload",
                    "title": doc["name"],
                    "content_snippet": snippet,
                    "score": score * 1.5 # Boost document title matches
                })

        # 2. Search Study Guides
        guide = db_manager.get_study_guide(workspace_id)
        if guide:
            for topic, content in guide["content"].items():
                score = 0
                topic_text = f"{topic} {content}".lower()
                for kw in keywords:
                    score += topic_text.count(kw)
                
                if score > 0:
                    snippet = content[:200] + "..." if len(content) > 200 else content
                    results.append({
                        "source": f"Study Guide ({guide['mode'].replace('_', ' ').title()})",
                        "title": topic,
                        "content_snippet": snippet,
                        "score": score
                    })

        # 3. Search Flashcards
        cards = db_manager.get_flashcards(workspace_id)
        for card in cards:
            score = 0
            card_text = f"{card['front']} {card['back']}".lower()
            for kw in keywords:
                score += card_text.count(kw)
                
            if score > 0:
                results.append({
                    "source": "Flashcard",
                    "title": f"Card #{card['id']}",
                    "content_snippet": f"Q: {card['front']} | A: {card['back']}",
                    "score": score * 0.8
                })

        # 4. Search Notes
        notes = db_manager.get_notes(workspace_id)
        if notes and notes.get("content"):
            score = 0
            notes_text = notes["content"].lower()
            for kw in keywords:
                score += notes_text.count(kw)
                
            if score > 0:
                snippet = notes_text[:200] + "..." if len(notes_text) > 200 else notes_text
                results.append({
                    "source": "My Notes",
                    "title": "Notes Editor",
                    "content_snippet": snippet,
                    "score": score * 2.0 # Boost personal notes matches
                })

        # Sort results by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
