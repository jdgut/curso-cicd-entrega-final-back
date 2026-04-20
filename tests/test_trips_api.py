from datetime import UTC, datetime, timedelta


def _register(client, email: str, role: str = "usuario"):
    return client.post(
        "/api/users/register",
        json={"email": email, "password": "password123", "role": role},
    )


def test_trip_creation_and_join_flow(client):
    _register(client, "creador@eafit.edu.co")
    _register(client, "amigo@eafit.edu.co")

    start_at = (datetime.now(UTC) + timedelta(minutes=30)).isoformat()
    created = client.post(
        "/api/trips",
        json={
            "actor_email": "creador@eafit.edu.co",
            "title": "Metro PM",
            "meeting_point": "Salida norte",
            "start_at": start_at,
            "transport_mode": "caminando",
            "direction": "metro_universidad",
        },
    )
    assert created.status_code == 200
    trip_id = created.json()["id"]

    joined = client.post(f"/api/trips/{trip_id}/join", json={"actor_email": "amigo@eafit.edu.co"})
    assert joined.status_code == 200
    assert len(joined.json()["participants"]) == 2


def test_trip_state_requires_permission(client):
    _register(client, "admin@eafit.edu.co", role="administrador")
    _register(client, "normal@eafit.edu.co")
    _register(client, "otro@eafit.edu.co")

    start_at = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
    created = client.post(
        "/api/trips",
        json={
            "actor_email": "normal@eafit.edu.co",
            "title": "Bus tarde",
            "meeting_point": "Paradero principal",
            "start_at": start_at,
            "transport_mode": "bus_universidad",
            "direction": "universidad_metro",
        },
    )
    trip_id = created.json()["id"]

    forbidden = client.post(
        f"/api/trips/{trip_id}/state",
        json={"actor_email": "otro@eafit.edu.co", "new_state": "en_desplazamiento_metro"},
    )
    assert forbidden.status_code == 403

    allowed = client.post(
        f"/api/trips/{trip_id}/state",
        json={"actor_email": "admin@eafit.edu.co", "new_state": "en_desplazamiento_metro"},
    )
    assert allowed.status_code == 200


def test_heatmap_endpoint(client):
    _register(client, "grafica@eafit.edu.co")
    start_at = (datetime.now(UTC) + timedelta(minutes=20)).isoformat()
    client.post(
        "/api/trips",
        json={
            "actor_email": "grafica@eafit.edu.co",
            "title": "Caminata manana",
            "meeting_point": "Plataforma metro",
            "start_at": start_at,
            "transport_mode": "caminando",
            "direction": "metro_universidad",
        },
    )

    response = client.get("/api/trips/metrics/heatmap")
    assert response.status_code == 200
    assert len(response.json()) == 2
