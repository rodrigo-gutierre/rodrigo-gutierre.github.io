# RJ Turismo

Site em **um único arquivo**: `index.php` (funciona em qualquer hospedagem com PHP; no GitHub Pages é convertido em HTML automaticamente).

- **Dados** (pacotes, hospedagens, experiências, destinos): importados da Central Tour por `atualizar.py` (`python atualizar.py index.php`). No GitHub, a ação *Atualizar e publicar* roda sozinha às 06h e 18h e a cada push.
- **Logo**: coloque `logo.png` (ou `.svg/.webp/.jpg`) ao lado do `index.php`. É detectado sozinho no topo, no rodapé e no ícone da aba.
- **Dados da agência** (telefone, WhatsApp, e-mail, cores, redes): bloco `$C` no início do `index.php`.
