from colorama import init, Fore, Style
init()

errorcode = F"{Fore.WHITE}[{Fore.RED}!{Fore.WHITE}]"
addcode = F"{Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]"
checkcode = F"{Fore.WHITE}[{Fore.YELLOW}~{Fore.WHITE}]"
foundcheck = F"{Fore.WHITE}[{Fore.MAGENTA}~{Fore.WHITE}]"

print(errorcode)
print(addcode)
print(checkcode)
print(foundcheck)