import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button
import re

# Imposta le variabili di configurazione
api_id = '25765102' # Sostituisci con il tuo api_id
api_hash = 'ea1f34752c0860fa799b4153da5c5554'  # Sostituisci con il tuo api_hash
bot_token = '2082565967:AAGhPEPgHnOD278B1aDm_Fv27ERPlebKGVU'  # Sostituisci con il token del bot di BotFather

# Crea un'istanza del client Telethon
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Dizionario per mappare gli ID ai rispettivi URL
game_url_map = {}

# Funzione per cercare i giochi
def search_games(title):
    search_url = f'https://fitgirl-repacks.site/?s={requests.utils.quote(title)}'
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    games = []
    for article in soup.select('article .entry-title a'):
        game_title = article.text.strip()
        game_url = article['href']
        games.append({'title': game_title, 'url': game_url})

    return games

# Funzione per ottenere il magnet link e le repack features
def get_game_details(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Estrazione del primo magnet link
    magnet_link = ''
    for a_tag in soup.find_all('a', href=True):
        if a_tag['href'].startswith('magnet:'):
            magnet_link = a_tag['href']
            break

    # Estrazione delle "Repack Features"
    repack_features = ''
    repack_header = soup.find('h3', text=re.compile(r'Repack Features', re.I))
    if repack_header:
        ul_tag = repack_header.find_next('ul')
        if ul_tag:
            # Raccoglie solo i testi degli li, evitando duplicazioni
            repack_features_list = []

            for li in ul_tag.find_all('li', recursive=False):  # Limita la ricerca solo ai li diretti
                feature = f"• {li.text.strip()}"
                repack_features_list.append(feature)

            repack_features = '\n'.join(repack_features_list)

    return magnet_link, repack_features

# Funzione per suddividere i messaggi lunghi in parti
def split_message(text, max_length=4096):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# Evento che mostra il pulsante "Cerca"
@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    buttons = [[Button.inline("Cerca", b"cerca")]]
    await event.respond('Benvenuto! Premi il pulsante "Cerca" per cercare un gioco.', buttons=buttons)

# Evento che gestisce il clic sul pulsante "Cerca" e modifica il messaggio
@client.on(events.CallbackQuery(data=b'cerca'))
async def search_prompt(event):
    await event.edit('Per favore, manda il titolo del gioco che vuoi cercare.')

# Evento che gestisce il messaggio di ricerca
@client.on(events.NewMessage)
async def search_command(event):
    # Se l'utente ha già inviato un comando, ignoriamo
    if event.text.startswith('/'):
        return

    query = event.message.text
    games = search_games(query)
    
    if games:
        buttons = []
        for index, game in enumerate(games):
            # Mappa l'ID (index) all'URL del gioco
            game_url_map[str(index)] = game['url']
            # Crea i bottoni con l'ID come data
            buttons.append([Button.inline(game['title'], str(index).encode('utf-8'))])

        await event.respond("Seleziona il gioco che vuoi vedere:", buttons=buttons)
    else:
        await event.respond('Nessun gioco trovato.')

# Evento che gestisce il clic sui bottoni dei giochi
@client.on(events.CallbackQuery)
async def game_selected(event):
    # Decodifica l'ID dal bottone cliccato
    game_id = event.data.decode('utf-8')
    
    # Recupera l'URL corrispondente dall'ID
    game_url = game_url_map.get(game_id)

    if game_url:
        # Ottieni i dettagli del gioco
        magnet_link, repack_features = get_game_details(game_url)

        # Risposta con i dettagli del gioco
        if magnet_link and repack_features:
            # Usa il magnet link come testo normale, non come link HTML
            response_text = f"<b>Magnet Link:</b> <code>{magnet_link}</code>\n\n"
            response_text += f"<b>Repack Features:</b>\n{repack_features}"
            
            # Spezza il messaggio in più parti se troppo lungo
            for part in split_message(response_text):
                await event.respond(part, parse_mode='html')  # Manda il messaggio formattato in HTML
        else:
            await event.edit('Non sono riuscito a trovare i dettagli del gioco o il magnet link.')
    else:
        await event.edit('Per favore, manda il titolo del gioco che vuoi cercare.')

# Avvia il bot
print("Il bot è in esecuzione...")
client.run_until_disconnected()