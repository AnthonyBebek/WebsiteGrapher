from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import func
from typing import List, Tuple
import FastLogger as logger
from colorama import init, Fore
import json  # Added for handling JSON strings
from datetime import datetime

errorcode = F"{Fore.WHITE}[{Fore.RED}!{Fore.WHITE}]{Fore.RED}"
addcode = F"{Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]{Fore.GREEN}"
checkcode = F"{Fore.WHITE}[{Fore.YELLOW}~{Fore.WHITE}]{Fore.YELLOW}"
foundcheck = F"{Fore.WHITE}[{Fore.MAGENTA}Server Info{Fore.WHITE}]{Fore.MAGENTA}"
IDCodeOpen = F"{Fore.WHITE}[{Fore.CYAN}Client: "
IDCodeClose = F"{Fore.WHITE}]"

class Websites(SQLModel, table=True):
    ID: int = Field(default=None, primary_key=True)
    Ref: str = Field(default="[]")
    LinksTo: str = Field(default=0)
    Checked: bool = Field(default=False)
    URL: str = Field(nullable=False, unique=True)
    StatusCode: int = Field(default=0)
    RobotsTxt: str = Field(default="Unknown")
    Country: str = Field(default="Unknown")
    Crawlable: bool = Field(default=False)
    LastChecked: datetime = Field(default=datetime.min)

class Pages(SQLModel, table=True):
    ID: int = Field(default=None, primary_key=True)
    SiteID: int = Field(nullable=False, foreign_key="websites.ID")
    Page: str = Field(default=None)
    Language: str = Field(default=None)
    category: str = Field(default=None)

class RobotsTxt(SQLModel, table=True):
    ID: int = Field(default=None, primary_key=True)
    SiteID: int = Field(nullable=False, foreign_key="websites.ID")
    Allowed: str = Field(default=None)
    Disallowed: str = Field(default=None)
    UserAgent: str = Field(default=None)
    LastFetched: datetime = Field(default=datetime.min)

engine = create_engine("sqlite:///database.db")

SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    exists = session.exec(
        select(Websites).where(Websites.URL == "https://www.similarweb.com/top-websites/")
    ).first()

    if not exists:
        session.add(Websites(URL="https://www.similarweb.com/top-websites/"))
        session.add(Websites(URL="https://www.semrush.com/website/top/"))
        session.commit()

def getUncheckedURL() -> str:
    '''
    Retrieves an unchecked URL from the database.
    Returns:
        str: An unchecked URL or None if none are available.
    '''

    try:
        with Session(engine) as session:
            statement = select(Websites).where(Websites.Checked == False).limit(1).order_by(func.random())
            result = session.exec(statement).first()
            if result:
                return result.URL
            else:
                logger.loggingWarning("No unchecked URLs available.")
                return None
    except Exception as e:
        logger.loggingError(f"Error retrieving unchecked URL: {e}")
        return None

def updateCheckedStatus(site_url: str) -> None:
    '''
    Updates the checked status of a URL in the database.
    Args:
        site_url (str): The URL to update.
    Returns:
        None
    '''
    # Handle case where site_url is a list
    if isinstance(site_url, list):
        site_url = site_url[0]
    try:
        with Session(engine) as session:
            statement = select(Websites).where(Websites.URL == site_url)
            result = session.exec(statement).first()
            if result:
                result.Checked = True
                session.add(result)
                session.commit()
    except Exception as e:
        logger.loggingError(f"Error updating checked status for {site_url}: {e}")

def addWebsite(link_url: str, new_page: str, urls: list, clientid: str) -> None:
    '''
    Adds a new website and its links to the database.
    Args:
        link_url (str): The URL of the website to add.
        urls (list): A list of URLs that the website links to.
        clientid (str): The ID of the client adding the website.
    Returns:
        None
    '''
    try:
        with Session(engine) as session:
            # Find ID from link_url
            statement = select(Websites).where(Websites.URL == link_url)
            result = session.exec(statement).first()
            if result:
                site_id = result.ID
            else:
                new_website = Websites(URL=link_url, Ref=json.dumps([]), Checked=False)
                session.add(new_website)
                session.commit()
                session.refresh(new_website)
                site_id = new_website.ID

            # Add new websites
            for url in urls:
                statement = select(Websites).where(Websites.URL == url)
                existing_website = session.exec(statement).first()
                if not existing_website:
                    new_website = Websites(
                        URL=url,
                        Ref=json.dumps([site_id]),  # Initialize with the current site_id
                        Checked=False
                    )
                    session.add(new_website)
                else:
                    # Update Ref to append the new site_id
                    existing_refs = json.loads(existing_website.Ref)
                    if site_id not in existing_refs:
                        existing_refs.append(site_id)
                        existing_website.Ref = json.dumps(existing_refs)
                        session.add(existing_website)

            session.commit()
    except Exception as e:
        logger.loggingError(f"Error adding website {link_url} by client {clientid}: {e}")

def batchAddWebsites(urls: List[str], page: str, link_url: str, clientid: str) -> List[Tuple[str, str]]:
    '''
    Adds a batch of websites to the database.
    Args:
        websites (list): A list of website URLs to add.
    Returns:
        None
    '''
    try:
        results = []
        if isinstance(urls, str):
            urls = [urls]

        with Session(engine) as session:
            # Get ID of link_url
            statement = select(Websites).where(Websites.URL == link_url)
            result = session.exec(statement).first()
            if result:
                site_id = result.ID

            # Prepare new websites to add
            for url in urls:
                website = session.exec(select(Websites).where(Websites.URL == url)).first()
                if not website:
                    new_website = Websites(
                        URL=url,
                        Ref=json.dumps([site_id]),  # Initialize with the current site_id
                        Checked=False,
                        LinksTo=site_id
                    )
                    session.add(new_website)
                    results.append((f"{addcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.GREEN} Added: {url}", "1-" + url))
                else:
                    # Update Ref to append the new site_id
                    existing_refs = json.loads(website.Ref)
                    if site_id not in existing_refs:
                        existing_refs.append(site_id)
                        website.Ref = json.dumps(existing_refs)
                        session.add(website)
                    results.append((f"{checkcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.YELLOW} URL Found: {url}", "0-" + url))
        # Add page content to link_url
            if page:
                page_entry = session.exec(select(Pages).where(Pages.SiteID == site_id)).first()
                if not page_entry:
                    new_page = Pages(
                        SiteID=site_id,
                        Page=page,
                        category=None
                    )
                    session.add(new_page)
                else:
                    page_entry.Page = page
                    session.add(page_entry)
            session.commit()
            logger.loggingInfo(f"Client {clientid} batch added {len(urls)} websites.")
    except Exception as e:
        logger.loggingError(f"Error batch adding websites by client {clientid}: {e}")

    return results