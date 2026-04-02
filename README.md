# NASA WALLPAPER - Gerenciador de Papel de Parede

Este projeto consiste em uma aplicação desktop que automatiza a alteração do papel de parede do Windows utilizando a API "Astronomy Picture of the Day" (APOD) da NASA.

## Funcionamento
O software realiza uma requisição aos servidores da NASA para obter a imagem astronômica do dia (ou o frame de um vídeo, caso não haja imagem estática). Além de baixar o arquivo em alta resolução, o sistema traduz a descrição técnica do objeto astronômico e permite que o usuário agende a atualização automática via Windows.

## Tecnologias Utilizadas
* Linguagem: Python 3.x
* Interface Gráfica: CustomTkinter
* Processamento de Imagens: Pillow
* Comunicação HTTP: Requests
* Integração com Sistema: Biblioteca ctypes (Win32 API) e Subprocess (CLI)

## Requisitos de Instalação

1. Certifique-se de ter o Python instalado em sua máquina.
2. Clone este repositório.
3. Instale as bibliotecas necessárias através do terminal:
   Bash
   pip install -r requirements.txt