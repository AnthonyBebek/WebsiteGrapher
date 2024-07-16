import locale
import time
import random
import DB
from colorama import init, Fore, Style
init()

locale.setlocale(locale.LC_ALL, '')

errorcode = F"{Fore.WHITE}[{Fore.RED}!{Fore.WHITE}]{Fore.RED}"
addcode = F"{Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]{Fore.GREEN}"
checkcode = F"{Fore.WHITE}[{Fore.YELLOW}~{Fore.WHITE}]{Fore.YELLOW}"
foundcheck = F"{Fore.WHITE}[{Fore.MAGENTA}~{Fore.WHITE}]{Fore.MAGENTA}"

def move_cursor(x, y):
    print(f'\x1b[{y};{x}H', end='')

print("\x1b[2J")

previous_Searched = 0
previous_timestamp = time.time() - 2
current_timestamp = time.time()

def get_database_stats():

    total_records = DB.get_sites_count()
    Unsearched = DB.get_sites_checked()
    Searched = int(total_records) - int(Unsearched)

    return total_records, Unsearched, Searched 

def print_database_stats(total_records, Unsearched, Searched):
    percent = round(int(Unsearched) / int(total_records)* 100, 2) 
    move_cursor(1, 1)
    total_records_formatted = locale.format_string("%d", int(total_records), grouping=True)
    print(f"Total Records: {Fore.GREEN}{total_records_formatted}{Fore.WHITE}")

    move_cursor(1, 2)
    unsearched_formatted = locale.format_string("%d", int(Unsearched), grouping=True)
    print(f"Unsearched: {Fore.CYAN}{unsearched_formatted}{Fore.WHITE}")

    move_cursor(1, 3)
    searched_formatted = locale.format_string("%d", int(Searched), grouping=True)
    print(f"Searched: {Fore.MAGENTA}{searched_formatted}{Fore.WHITE}")

    move_cursor(1, 4)
    print(f"--------------------------------------------------")

    move_cursor(1, 5)
    print(f"Percent not searched: {Fore.YELLOW}{percent}%{Fore.WHITE}", end='')