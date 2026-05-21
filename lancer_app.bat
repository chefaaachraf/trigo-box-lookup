@echo off
cd /d "%~dp0"
echo Demarrage du serveur TRIGO BoxApp...
start "TRIGO - Serveur" python server.py
echo Attente du demarrage (5 secondes)...
timeout /t 5 /nobreak >nul
echo Ouverture du tunnel iPhone...
start "TRIGO - Tunnel iPhone" cmd /k "ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 serveo.net"
echo.
echo Les deux fenetres sont ouvertes.
echo - Fenetre SERVEUR : le serveur FastAPI
echo - Fenetre TUNNEL  : l'URL pour l'iPhone (en vert)
echo.
echo Fermez ces fenetres pour tout arreter.
