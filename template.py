import os
structure = {
    "pod_containers":{
        "gateway":{
            "src":{
                "__init__.py":None,
                "main.py":None,
                "router.py":None,
                "core":{
                    "connectors":{
                        "__init__.py":None,
                        "database_connector.py":None,
                        "llm_connector.py":None
                    },
                    "services":{
                        "__init__.py":None,
                        "session.py":None,
                        "login.py":None
                    },
                    "storage":{

                    },
                    "utils":{
                        "__init__.py":None,
                        "config.py":None,
                        "utils.py":None
                    }
                }
            },
            "Dockerfile":None,
            "requirements.txt":None,
        },
        "mcp_server":{
            "src":{
                "__init__.py":None,
                "main.py":None,
            },
            "Dockerfile":None,
            "requirements.txt":None,
        },
        "text_to_sql":{
            "src":{
                "__init__.py":None,
                "main.py":None,
                "core":{
                    "connectors":{
                        "__init__.py":None,
                        "database_connector.py":None,
                        "llm_connector.py":None,
                        "mcp_client.py":None
                    },
                    "prompts":{

                    },
                    "services":{
                        "__init__.py":None,
                        "graph.py":None,
                        "chat.py":None
                    },
                    "storage":{

                    },
                    "utils":{
                        "__init__.py":None,
                        "config.py":None,
                        "utils.py":None
                    }
                }
            },
            "Dockerfile":None,
            "requirements.txt":None,
        },
        "frontend":{}
    },
    ".gitignore":None,
    "docker-compose.yml":None,
    "README.md":None
}

def create_structure(base_path,structure):
    for name,content in structure.items():
        path = os.path.join(base_path,name)
        if content is None:
            with open(path,"w") as f:
                f.write("")
        else:
            os.makedirs(path,exist_ok=True)
            create_structure(path,content)


base_directory = "."
create_structure(base_directory,structure)
print("Directory created.")