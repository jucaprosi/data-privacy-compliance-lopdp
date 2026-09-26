import os
from typing import Dict

class NIIF18DoctrineService:
    def __init__(self, doctrine_path: str = None):
        if not doctrine_path:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.doctrine_path = os.path.join(current_dir, "biblioteca_doctrinal")
        else:
            self.doctrine_path = doctrine_path
            
    def get_all_doctrine(self) -> Dict[str, str]:
        """
        Lee todos los archivos markdown de la biblioteca doctrinal
        y devuelve un diccionario con el nombre del archivo y su contenido.
        """
        doctrine = {}
        if not os.path.exists(self.doctrine_path):
            return doctrine
            
        for filename in sorted(os.listdir(self.doctrine_path)):
            if filename.endswith(".md"):
                file_path = os.path.join(self.doctrine_path, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    doctrine[filename] = f.read()
                    
        return doctrine

    def get_doctrine_context(self) -> str:
        """
        Devuelve todo el conocimiento doctrinal concatenado como un bloque de texto
        para ser inyectado en el contexto (RAG/Prompt).
        """
        docs = self.get_all_doctrine()
        context_parts = []
        for filename, content in docs.items():
            context_parts.append(f"--- Documento: {filename} ---\n{content}\n")
        
        return "\n".join(context_parts)
