import ast, re
from pathlib import PurePosixPath

def analyze_source(path: str, source: str) -> dict:
    lang=language_for(path); symbols=[]; imports=[]; complexity=0; parser="fallback"
    if lang=="Python":
        try:
            tree=ast.parse(source); parser="python-ast"
            for node in ast.walk(tree):
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                    symbols.append({"name":node.name,"type":"class" if isinstance(node,ast.ClassDef) else "function","start_line":node.lineno,"end_line":getattr(node,"end_lineno",node.lineno),"signature":node.name})
                elif isinstance(node,ast.Import): imports.extend(a.name for a in node.names)
                elif isinstance(node,ast.ImportFrom) and node.module: imports.append(("../"*max(0,node.level-1)+"./" if node.level else "")+node.module.replace(".","/"))
                if isinstance(node,(ast.If,ast.For,ast.AsyncFor,ast.While,ast.IfExp,ast.ExceptHandler,ast.comprehension)): complexity+=1
                if isinstance(node,ast.BoolOp): complexity+=max(0,len(node.values)-1)
        except SyntaxError: pass
    else:
        # Tree-sitter is used when a bundled grammar is available; regex remains a safe fallback.
        try:
            from tree_sitter_language_pack import get_parser
            parser_obj=get_parser(lang.lower())
            try: tree=parser_obj.parse(source)
            except TypeError: tree=parser_obj.parse(source.encode("utf-8"))
            root=getattr(tree,"root_node",None)
            if callable(root): root=root()
            parser="tree-sitter"
            patterns={"javascript":("function_declaration","class_declaration","method_definition","arrow_function"),"typescript":("function_declaration","class_declaration","method_definition","arrow_function"),"tsx":("function_declaration","class_declaration","method_definition","arrow_function"),"java":("method_declaration","class_declaration","constructor_declaration"),"go":("function_declaration","method_declaration","type_declaration"),"rust":("function_item","struct_item","enum_item","impl_item")}
            wanted=set(patterns.get(lang.lower(),()))
            raw=source.encode("utf-8")
            def value(node,key):
                v=getattr(node,key,None)
                return v() if callable(v) else v
            def walk(n):
                kind=value(n,"type") or value(n,"kind")
                if kind in wanted:
                    name_node=None
                    try: name_node=n.child_by_field_name("name")
                    except Exception: pass
                    if name_node is None:
                        children=value(n,"children")
                        if children is None: children=[n.child(i) for i in range(value(n,"child_count") or 0)]
                        name_node=next((c for c in children if c and ("identifier" in (value(c,"type") or value(c,"kind") or "") or (value(c,"type") or value(c,"kind")) in {"name","type_identifier"})),None)
                    if name_node:
                        start=value(n,"start_byte") or 0; end=value(n,"end_byte") or start
                        start_line=raw[:start].count(b"\n")+1; end_line=raw[:end].count(b"\n")+1
                        ns=value(name_node,"start_byte") or 0; ne=value(name_node,"end_byte") or ns
                        name=raw[ns:ne].decode("utf-8",errors="replace")
                        source_lines=source.splitlines();signature=source_lines[start_line-1][:240] if start_line<=len(source_lines) else name
                        symbols.append({"name":name,"type":"class" if any(x in kind for x in ("class","struct","enum")) else "function","start_line":start_line,"end_line":end_line,"signature":signature})
                children=value(n,"children")
                if children is None: children=[n.child(i) for i in range(value(n,"child_count") or 0)]
                for child in children:
                    if child is not None: walk(child)
            if root is not None: walk(root)
        except Exception: pass
        if not symbols:
            for i,line in enumerate(source.splitlines(),1):
                m=re.match(r"\s*(?:export\s+)?(?:async\s+)?function\s+([\w$]+)|\s*class\s+([\w$]+)|\s*(?:export\s+)?(?:const|let|var)\s+([\w$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",line)
                if m:
                    name=next(g for g in m.groups() if g); symbols.append({"name":name,"type":"class" if "class" in line else "function","start_line":i,"end_line":i,"signature":line.strip()[:240]})
        for m in re.finditer(r'''(?:import\s+(?:.+?\s+from\s+)?|require\()(["\'])([^"\']+)\1''',source): imports.append(m.group(2))
        complexity=sum(len(re.findall(r"\b(if|for|while|case|catch)\b|&&|\|\|",x)) for x in source.splitlines())
    lines=source.splitlines()
    symbols=sorted(symbols,key=lambda s:s["start_line"])[:10000]
    for s in symbols:
        if s["end_line"]==s["start_line"]:
            later=[x["start_line"] for x in symbols if x["start_line"]>s["start_line"]]
            s["end_line"]=(min(later)-1) if later else len(lines)
    return {"language":lang,"symbols":symbols,"imports":sorted(set(imports)),"complexity":complexity+1,"line_count":len(lines),"parser":parser}

def language_for(path):
    return {".py":"Python",".pyi":"Python",".js":"JavaScript",".jsx":"JavaScript",".mjs":"JavaScript",".cjs":"JavaScript",".ts":"TypeScript",".tsx":"TSX",".java":"Java",".go":"Go",".rs":"Rust",".rb":"Ruby",".php":"PHP",".cs":"C#",".c":"C",".h":"C/C++",".cc":"C++",".cpp":"C++",".hpp":"C++",".swift":"Swift",".kt":"Kotlin",".kts":"Kotlin",".scala":"Scala",".vue":"Vue",".svelte":"Svelte",".html":"HTML",".css":"CSS",".scss":"SCSS",".json":"JSON",".yaml":"YAML",".yml":"YAML",".toml":"TOML",".md":"Markdown",".sql":"SQL",".sh":"Shell"}.get(PurePosixPath(path).suffix.lower(),"Other")
