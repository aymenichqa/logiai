"""Tests de sécurité : authentification (401) et autorisation (403)."""
from logiai import config


def test_health_reste_public(client):
    assert client.get("/health").status_code == 200


def test_predict_sans_cle_refuse(client, livraison_valide):
    # Exemple fourni : écrivez les suivants sur ce modèle.
    r = client.post("/v1/predict", json=livraison_valide)
    assert r.status_code == 401


def test_predict_cle_invalide_refuse(client, livraison_valide):
    r = client.post("/v1/predict", json=livraison_valide, headers={"X-API-Key": "fausse-cle"})
    assert r.status_code == 401


def test_predict_cle_vide_refuse(client, livraison_valide):
    r = client.post("/v1/predict", json=livraison_valide, headers={"X-API-Key": ""})
    assert r.status_code == 401


def test_predict_cle_utilisateur_accepte(client, headers_user, livraison_valide):
    r = client.post("/v1/predict", json=livraison_valide, headers=headers_user)
    assert r.status_code == 200


def test_predict_cle_admin_accepte(client, headers_admin, livraison_valide):
    r = client.post("/v1/predict", json=livraison_valide, headers=headers_admin)
    assert r.status_code == 200


def test_model_info_sans_cle_refuse(client):
    assert client.get("/v1/model-info").status_code == 401


def test_model_info_cle_utilisateur_interdite(client, headers_user):
    # 403 et non 401 : la clé est valide, mais le rôle ne suffit pas
    assert client.get("/v1/model-info", headers=headers_user).status_code == 403


def test_model_info_cle_admin_accepte(client, headers_admin):
    r = client.get("/v1/model-info", headers=headers_admin)
    assert r.status_code == 200
    assert "version" in r.json()


def test_la_reponse_401_ne_revele_pas_la_cle(client, livraison_valide):
    r = client.post("/v1/predict", json=livraison_valide)
    assert r.status_code == 401
    assert config.API_KEY not in r.text
    assert config.ADMIN_KEY not in r.text


def test_sans_configuration_tout_est_refuse(client, livraison_valide, monkeypatch):
    # échec sûr : sans clés dans l'environnement, aucune valeur ne doit passer
    monkeypatch.setattr(config, "API_KEY", None)
    monkeypatch.setattr(config, "ADMIN_KEY", None)
    for entetes in ({}, {"X-API-Key": "cle-test-utilisateur"}, {"X-API-Key": "cle-test-admin"}):
        assert client.post("/v1/predict", json=livraison_valide, headers=entetes).status_code == 401


def test_ordre_des_controles_cle_avant_donnees(client, livraison_valide):
    # la clé est vérifiée AVANT le schéma : 401, pas 422, même avec une pluie impossible
    livraison_valide["pluie_mm"] = 500
    assert client.post("/v1/predict", json=livraison_valide).status_code == 401
