def test_register_user_success(client):
    response = client.post(
        "/api/users/register",
        json={
            "email": "estudiante@eafit.edu.co",
            "password": "password123",
            "role": "usuario",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "estudiante@eafit.edu.co"
    assert body["role"] == "usuario"


def test_register_user_domain_error(client):
    response = client.post(
        "/api/users/register",
        json={
            "email": "invalido@gmail.com",
            "password": "password123",
            "role": "usuario",
        },
    )

    assert response.status_code == 422

def test_register_user_exists_error(client):
    # crear el usuario por primera vez
    response = client.post(
        "/api/users/register",
        json={
            "email": "prueba_existe@eafit.edu.co",
            "password": "password123",
            "role": "usuario",
        },
    )
    # validar que se creó correctamente
    assert response.status_code == 200
    
    # intentar crear el mismo usuario nuevamente
    response = client.post(
        "/api/users/register",
        json={
            "email": "prueba_existe@eafit.edu.co",
            "password": "password123",
            "role": "usuario",
        },
    )
    # validar que se recibió un error de conflicto por usuario existente
    assert response.status_code == 409


def test_login_user_success(client):
    client.post(
        "/api/users/register",
        json={
            "email": "existente@eafit.edu.co",
            "password": "password123",
            "role": "usuario",
        },
    )

    login_response = client.post(
        "/api/users/login",
        json={
            "email": "existente@eafit.edu.co",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["email"] == "existente@eafit.edu.co"


def test_login_user_invalid_password(client):
    client.post(
        "/api/users/register",
        json={
            "email": "existente2@eafit.edu.co",
            "password": "password123",
            "role": "usuario",
        },
    )

    login_response = client.post(
        "/api/users/login",
        json={
            "email": "existente2@eafit.edu.co",
            "password": "password999",
        },
    )

    assert login_response.status_code == 401


def test_cors_preflight_allows_frontend_origin(client):
    response = client.options(
        "/api/trips/metrics/heatmap/simulated",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in {200, 204}
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
