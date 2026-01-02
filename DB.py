from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import func
from typing import List, Tuple
import Logger as logger
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
    RobotsTxt: bool = Field(default=False)
    Country: str = Field(default="Unknown")
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
    Allowed: str = Field(default="[]")
    Disallowed: str = Field(default="[]")
    UserAgent: str = Field(default="*")
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
        session.add(Websites(URL="https://www.imdb.com"))
        session.add(Websites(URL="https://www.wikipedia.org"))
        session.add(Websites(URL="https://www.dailymotion.com"))
        session.add(Websites(URL="https://www.gravatar.com"))
        session.add(Websites(URL="https://www.bbc.com"))
        session.add(Websites(URL="https://www.cnn.com"))
        session.add(Websites(URL="https://www.nytimes.com"))
        session.add(Websites(URL="https://www.theguardian.com/international"))


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

def updateCheckedStatus(site_url: str, status_code: int) -> None:
    '''
    Updates the checked status and status code of a URL in the database.
    Args:
        site_url (str): The URL to update.
        status_code (int): The HTTP status code to record.
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
                result.StatusCode = status_code
                result.LastChecked = datetime.now()
                session.add(result)
                session.commit()
    except Exception as e:
        logger.loggingError(f"Error updating checked status for {site_url}: {e}")

def addWebsite(link_url: str, new_page: str, urls: list, clientid: str, status_code: int) -> None:
    '''
    Adds a new website and its links to the database.
    Args:
        link_url (str): The URL of the website to add.
        urls (list): A list of URLs that the website links to.
        clientid (str): The ID of the client adding the website.
        status_code (int): The HTTP status code of the website.
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
                result.StatusCode = status_code  # Update the status code
                session.add(result)
            else:
                new_website = Websites(URL=link_url, Ref=json.dumps([]), Checked=False, StatusCode=status_code)
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
        urls (list): A list of website URLs to add.
        page (str): The content of the page.
        link_url (str): The URL linking to the websites.
        clientid (str): The ID of the client adding the websites.
    Returns:
        List[Tuple[str, str]]: Results of the operation.
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
                        Language="Unknown",  # Default value for Language
                        category="Unknown"  # Default value for category
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

def createRobotsTxt(site_url: str, allowed: list, disallowed: list, user_agent: str) -> None:
    '''
    Creates a new robots.txt entry in the database.

    Params:
        site_url: str - The URL of the site.
        allowed: list - Allowed paths as a list.
        disallowed: list - Disallowed paths as a list.
        user_agent: str - User agent the rules apply to.
    Returns:
        None
    '''
    try:
        with Session(engine) as session:
            # Get site ID from site_url
            statement = select(Websites).where(Websites.URL == site_url)
            result = session.exec(statement).first()
            if result:
                site_id = result.ID
            else:
                raise ValueError(f"Site URL {site_url} not found in database")

            new_robots_txt = RobotsTxt(
                SiteID=site_id,
                Allowed=json.dumps(allowed),  # Store as JSON string
                Disallowed=json.dumps(disallowed),  # Store as JSON string
                UserAgent=user_agent,
                LastFetched=datetime.now()
            )
            session.add(new_robots_txt)
            statement = select(Websites).where(Websites.URL == site_url)
            result = session.exec(statement).first()
            if result:
                result.RobotsTxt = True
                session.add(result)
                session.commit()
            session.commit()
    except Exception as e:
        logger.loggingError(f"Error creating robots.txt for site {site_url}: {e}")

def getRobotsTxt(site_id: int) -> dict:
    '''
    % Retrieves the robots.txt rules for a given site.
    %
    Params:
        site_id: int - The ID of the site.
    Returns:
        dict: The robots.txt rules or None if not found.
    '''
    try:
        with Session(engine) as session:
            statement = select(RobotsTxt).where(RobotsTxt.SiteID == site_id)
            result = session.exec(statement).first()
            if result:
                return {
                    'allowed': result.Allowed,
                    'disallowed': result.Disallowed,
                    'user_agent': result.UserAgent,
                    'last_fetched': result.LastFetched
                }
            return None
    except Exception as e:
        logger.loggingError(f"Error retrieving robots.txt for site {site_id}: {e}")
        return None