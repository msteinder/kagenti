base_url = "http://localhost:8080"
admin_username = "admin"
admin_password = "admin"
demo_realm_name = "demo2"

from keycloak import KeycloakAdmin, KeycloakPostError

keycloak_admin = KeycloakAdmin(
            server_url=base_url,
            username=admin_username,
            password=admin_password,
            realm_name=demo_realm_name,
            user_realm_name='master')

# Create the demo realm
try:
    keycloak_admin.create_realm(
        payload={
            "realm": demo_realm_name,
            "enabled": True
        },
        skip_exists=True
    )

    print(f'Created realm "{demo_realm_name}"')
except KeycloakPostError as e:
    print(f'Realm "{demo_realm_name}" already exists')

test_user_name = "test"

# Add test user
try:
    keycloak_admin.create_user({
        "username": test_user_name,
        "firstName": test_user_name,
        "lastName": test_user_name,
        "email": "test@test.com",
        "emailVerified": True,
        "enabled": True,
        "credentials": [{"value": "test_password", "type": "password",}]
    })

    print(f'Created user "{test_user_name}"')
except KeycloakPostError as e:
    print(f'User "{test_user_name}" already exists')

# Create llama-stack client
external_tool_client_name = "my-external-tool"
try:
    keycloak_admin.create_client({
        "clientId": external_tool_client_name,
        "standardFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "fullScopeAllowed": False,
    })

    print(f'Created client "{external_tool_client_name}"')
except KeycloakPostError as e:
    print(f'Client "{external_tool_client_name}" already exists')

# Create tool-audience client scope
tool_audience_client_scope_name = "tool-audience"
tool_audience_client_scope_id = ""
try:
    tool_audience_client_scope_id = keycloak_admin.create_client_scope({
        "name": tool_audience_client_scope_name,
        "protocol": "openid-connect",
        "protocolMappers": [
            {
                "name": tool_audience_client_scope_name,
                "protocol": "openid-connect",
                "protocolMapper": "oidc-audience-mapper",
                "config": {
                    "access.token.claim": "true",
                    "id.token.claim": "false",
                    "included.client.audience": "my-external-tool",
                    "introspection.token.claim": "true",
                    "lightweight.claim": "false"
                },
            }
        ]
    })

    print(f'Created client scope "{tool_audience_client_scope_name}"')

    keycloak_admin.add_default_optional_client_scope(tool_audience_client_scope_id)
except KeycloakPostError as e:
    print(f'Client scope "{tool_audience_client_scope_name}" already exists')

# Create llama-stack client
llama_stack_client_name = "llama-stack"
llama_stack_client_id = ""
try:
    llama_stack_client_id = keycloak_admin.create_client({
        "clientId": llama_stack_client_name,
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "fullScopeAllowed": False,
        "publicClient": True # Disable client authentication
    })

    print(f'Created client "{llama_stack_client_name}"')
except KeycloakPostError as e:
    print(f'Client "{llama_stack_client_name}" already exists')

# If there is no llama-stack client ID, then there is an existing client
# Fetch the existing client to get the client ID
if llama_stack_client_id == "":
    try:
        client_search = keycloak_admin.get_clients()
    except KeycloakPostError as e:
        print(f'Cannot get client ID for "{llama_stack_client_name}: {e}')
        exit

    if "id" in client_search:
        llama_stack_client_id = client_search["id"]

    for client in client_search:
        if "clientId" in client and client["clientId"] == llama_stack_client_name:
            if "id" in client:
                llama_stack_client_id = client["id"]
                break

# If there is no tool-audience client scope ID, then there is an existing client scope
# Fetch the existing client scope to get the client scope ID
if tool_audience_client_scope_id == "":
    try:
        client_scope_search = keycloak_admin.get_client_scope_by_name(tool_audience_client_scope_name)
    except KeycloakPostError as e:
        print(f'Cannot get client scope ID for "{tool_audience_client_scope_name}')
        exit

    if "id" in client_scope_search:
        tool_audience_client_scope_id = client_scope_search["id"]

# Add the tool-audience client scope to the llama-stack client
try:
    keycloak_admin.add_client_optional_client_scope(
        llama_stack_client_id,
        tool_audience_client_scope_id,
        payload={
            "realm": demo_realm_name,
            "client": llama_stack_client_name,
            "clientScopeId": tool_audience_client_scope_id
        }
    )

    print(f'Added client scope "{tool_audience_client_scope_name}" to client {llama_stack_client_name}')
except KeycloakPostError as e:
    print(f'Cannot client scope "{tool_audience_client_scope_name}" to client {llama_stack_client_name}: {e}')

