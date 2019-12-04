class RepoConfig:
    def __init__(self, config={}, defaults={}):
        self.config = config
        self.defaults = defaults

    def get_headers_for_path(self, path_to_match):
        '''
        Determine the headers that apply to particular file
        '''

        # Don't think I need a deep copy here
        resolved_headers = self.defaults.get('headers', {}).copy()

        # Get the first header_cfg whose path matches the object path, return an empty dict if no match
        first_matching_cfg = find_first_matching_cfg(self.config.get('headers', []), path_to_match)

        if first_matching_cfg:
            headers = first_value(first_matching_cfg)
            
            for key, value in headers.items():
                # Set/replace the header value for the header
                # The latest header with a matching path wins, this is important!
                resolved_headers[key.strip().lower()] = value.strip()

        return resolved_headers

def find_first_matching_cfg(headers, path_to_match):
    return next((header_cfg for header_cfg in headers if match_path(first_key(header_cfg), path_to_match)), {})

def match_path(cfg_path, path_to_match):
    # normalize the paths by removing leading slash since that will
    # result in a leading empty string with 'split'ing
    cfg_path = strip_prefix('/', cfg_path)
    path_to_match = strip_prefix('/', path_to_match)

    cfg_parts = cfg_path.split('/')
    path_parts = path_to_match.split('/')

    for idx, cfg_part in enumerate(cfg_parts):
        if cfg_part == '*':
            return True

        if cfg_part.startswith(':'):
            continue
        
        if len(path_parts) <= idx:
            return False
        
        if cfg_part.startswith('*.'):
          cfg_part_ext = cfg_part.split('.')[-1]
          last_path_part = path_parts[-1]
          last_path_ext = last_path_part.split('.')[-1]
          return last_path_ext == cfg_part_ext
        
        path_part = path_parts[idx]
        
        if path_part != cfg_part:
            return False
    
    if len(path_parts) > len(cfg_parts):
        return False
    
    return True

def first_key(dikt):
    # return dikt.keys()[0]
    return next(key for key in dikt)

def first_value(dikt):
    # return dikt.values()[0]
    return next(value for value in dikt.values())

def strip_prefix(prefix, path):
    # Copied from models.py::remove_prefix
    return path[len(prefix):] if path.startswith(prefix) else path