def is_valid_content(text: str, allowed: list[str], forbidden: list[str])->bool:
        if not text:
            return False
        
        if forbidden:
            f_list = [w.strip().lower() for w in forbidden if w.strip()]
            if any(word in text for word in f_list):
                return False
        
        if allowed:
            a_list = [w.strip().lower() for w in allowed if w.strip()]
            if a_list:
                return any(word in text for word in a_list)
                  
        return True