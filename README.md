# Bootcamp Cloud para Dados 🚀

Este repositório contém os resumos e implementações práticas das aulas do **Bootcamp Cloud para Dados (Jornada de Dados)**.  

---

## 📌 Aula 01 – Introdução ao Projeto e Estrutura na AWS

- 🚕 **Dataset Uber NYC**: análise de corridas de setembro/2014.  
- ☁️ **Infraestrutura em AWS**:
  - **S3** como repositório de dados brutos.  
  - **EC2** para execução do ambiente e publicação do app.  
  - **S3 Website Hosting**: configuração e publicação de **site estático** diretamente no bucket.  
- 🐍 **Stack utilizada**:
  - Python, Pandas, Numpy  
  - Streamlit para visualização  
  - Altair e PyDeck para gráficos e mapas interativos  
- 🔄 **Engenharia de Dados aplicada**:
  - Ingestão e limpeza dos dados.  
  - Criação de colunas de tempo (hora, dia da semana, data).  
  - Camadas de transformação: *raw → clean → analysis*.  
- 📊 **Dashboard interativo**:
  - KPIs básicos (corridas, datas, bases).  
  - Gráfico por hora do dia.  
  - Mapa com heatmap + pontos georreferenciados.  
  - Filtros dinâmicos (período, hora, base).  
- 🌐 **Site estático no S3**:
  - Configuração de bucket para hospedagem.  
  - Upload de arquivos HTML/CSS.  
  - Acesso público via endpoint do S3.  
- 💡 **Aprendizado principal**:  
  Estruturar dados em nuvem e disponibilizá-los tanto em um **app interativo (Streamlit no EC2)** quanto em um **site estático (S3)**, unindo **engenharia de dados** e **cloud**.

---

📌 *Conforme avanço nas próximas aulas, este README será atualizado com novos tópicos e implementações.*
