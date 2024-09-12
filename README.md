# **BookWorm - Sistema de Recomendação de Livros**

## **Sumário**
1. [Introdução](#introdução)
2. [Instalação](#instalação)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [Funcionalidades Principais](#funcionalidades-principais)
5. [Descrição dos Arquivos](#descrição-dos-arquivos)
6. [Como Usar](#como-usar)
7. [Detalhes Técnicos](#detalhes-técnicos)
8. [Exemplos de Uso](#exemplos-de-uso)

---

## **Introdução**
Este projeto é um sistema de recomendação de livros que permite aos usuários inserir livros conhecidos ou desconhecidos, gerar recomendações baseadas em similaridade textual (descrição do livro), e visualizar gráficos (histogramas) com livros semelhantes.

O sistema usa técnicas de processamento de linguagem natural (NLP), como **TF-IDF** e **similaridade de cosseno** para encontrar livros parecidos, e permite visualizar essas recomendações em um **histograma**.

---

## **Instalação**
Para executar o projeto em sua máquina, siga as instruções abaixo:

### **Requisitos**
1. **Python 3.7+**
2. Instale as bibliotecas necessárias com o seguinte comando:
    ```bash
    pip install -r requirements.txt
    ```

### **Configurações Iniciais**
1. Baixe ou clone este repositório:
   ```bash
   git clone <link do repositório>
   ```
2. Certifique-se de que o arquivo **dados.csv** está presente no diretório correto com a codificação UTF-8.

---

## **Estrutura do Projeto**
| Caminho/Arquivo               | Descrição                                                                 |
|-------------------------------|---------------------------------------------------------------------------|
| `/app.py`                      | Arquivo principal que inicializa a aplicação Flask                        |
| `/routes/chat.py`              | Controla a lógica de conversação com o bot, incluindo AIML e interações   |
| `/routes/recommendations.py`   | Gera as recomendações e gráficos para os usuários                         |
| `/routes/wordcloud.py`         | Gera a nuvem de palavras dos livros selecionados                          |
| `/routes/histograma.py`        | Gera e exibe o histograma de similaridade dos livros                      |
| `/utils.py`                    | Contém as funções principais de processamento de dados e NLP              |
| `/dados.csv`                   | Banco de dados de livros contendo títulos, descrições e autores           |
| `/templates/*.html`            | Arquivos de interface (HTML) para a renderização das páginas              |

---

## **Funcionalidades Principais**
- **Recomendação de Livros**: O usuário pode inserir um livro e receber recomendações baseadas em descrições.
- **Histograma de Similaridade**: Geração de um gráfico com os livros mais similares ao indicado pelo usuário.
- **Nuvem de Palavras**: Visualização de uma WordCloud com as palavras mais comuns nas descrições de livros.
- **Filtragem por Autor**: O sistema pode dar preferência a livros do mesmo autor se o usuário desejar.

---

## **Descrição dos Arquivos**

### **1. `app.py`**
Arquivo principal da aplicação que inicializa o servidor Flask. Ele carrega as rotas e define o comportamento da aplicação.

### **2. `chat.py`**
Este arquivo contém a lógica de interação com o bot de recomendação de livros. O bot se comunica via AIML e processa as respostas do usuário. Ele também é responsável por redirecionar para a página de recomendações após coletar informações suficientes.
- [Chat.py](./routes/chat.py)

### **3. `recommendations.py`**
Gera as recomendações de livros com base no título fornecido pelo usuário. Além disso, permite que o usuário visualize um histograma com os livros mais similares.
- [Recommendations.py](./routes/recommendations.py)

### **4. `utils.py`**
Arquivo que contém todas as funções principais do projeto, incluindo processamento de texto, cálculo de similaridade entre livros, geração de histogramas e WordClouds.
- [Utils.py](./utils.py)

### **5. `wordcloud.py`**
Gera uma WordCloud com as palavras mais comuns das descrições dos livros recomendados.
- [WordCloud.py](./routes/wordcloud.py)

### **6. `histograma.py`**
Responsável por gerar o histograma que mostra a similaridade entre os livros recomendados e o livro base.
- [Histograma.py](./routes/histograma.py)

### **7. `dados.csv`**
Arquivo que contém o banco de dados dos livros, com colunas como título, descrição e autor.

---

## **Como Usar**

### **1. Iniciar o Servidor**
Para rodar o servidor Flask, execute o seguinte comando:
```bash
python app.py
```

### **2. Interação com o Bot**
Abra o navegador e acesse o seguinte endereço:
```
http://localhost:5000
```
O bot começará perguntando se o usuário deseja uma recomendação de livro. A partir daí, você pode inserir o nome de um livro e seguir o fluxo.

### **3. Gerar Recomendação**
Após a interação inicial, o bot gera até 5 recomendações de livros semelhantes. O usuário pode solicitar um histograma de similaridade ou visualizar detalhes sobre um livro específico.

### **4. Ver Nuvem de Palavras**
Depois de selecionar um livro, o bot perguntará se o usuário deseja ver uma WordCloud. Se o usuário aceitar, será gerada uma WordCloud da descrição do livro.

---

## **Detalhes Técnicos**
- **NLP**: O projeto usa **TF-IDF** para vetorização de descrições de livros e **similaridade de cosseno** para encontrar livros mais similares.
- **Filtros por Autor**: O sistema pode aumentar a similaridade se o autor do livro for o mesmo, aplicando um fator de peso de 20%.
- **Histograma**: Um histograma de similaridade é gerado, mostrando os livros mais parecidos.

---

## **Exemplos de Uso**

### **1. Gerar Recomendação**
- **Entrada**: "Harry Potter e a Pedra Filosofal"
- **Saída**: Lista de 5 livros recomendados com base na descrição de "Harry Potter".

### **2. Gerar Histograma**
- **Comando**: "Sim" quando o bot pergunta sobre o histograma.
- **Resultado**: Um gráfico exibindo os livros mais similares ao livro fornecido.

---

Se tiver dúvidas ou problemas, sinta-se à vontade para abrir uma issue ou contribuir com o projeto!

---
