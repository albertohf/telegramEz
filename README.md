# Deploy no Portainer

Instruções rápidas para rodar este projeto no Portainer usando `docker-compose`.

- Faça upload deste repositório para o servidor onde o Docker/Portainer roda, ou copie os arquivos.
- Em Portainer: Stacks -> Add Stack -> cole o conteúdo de `docker-compose.yml` ou envie o arquivo.
- Verifique se o arquivo de sessão `meusession.session` está disponível no diretório do projeto no host. O `docker-compose.yml` atual faz bind mount de `./meusession.session` para `/app/meusession.session`.

Comandos alternativos no host (SSH/terminal):

```bash
docker compose up -d --build
```

Para parar e remover:

```bash
docker compose down
```

Observações:

- Se preferir, no Portainer você pode ajustar volumes para usar um volume nomeado em vez de bind mount.
- Garanta que `requirements.txt` esteja atualizado com as dependências necessárias.
