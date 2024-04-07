from typing import List, TypedDict
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from unidecode import unidecode
from enum import StrEnum
import os


class URL(StrEnum):
    """
    O2 FAMILY URL's
    >>> types
    ...     LOGIN -- login page,
    ...     OVERVIEW -- dashboard,
    ...     INVOICES -- invoice list
    ...     INVOICE_DETAIL_ -- URL to invoice, invoice number required after
    """

    LOGIN = "https://moje.o2family.cz/"
    OVERVIEW = "https://moje.o2family.cz/rychly-prehled"
    INVOICES = "https://moje.o2family.cz/vyuctovani-a-prehledy"
    INVOICE_DETAIL_ = "https://moje.o2family.cz/vyuctovani-a-prehledy/detail-faktury/"


class Contract(TypedDict):
    uuid: str
    tariff: str




class Invoice(TypedDict):
    invoice_number: int
    title: str
    href: str | None
    created: datetime
    due_date: datetime
    amount_CZK: float
    status: str
    paid: bool


# class INVCE_item_contract_units(TypedDict):
#     title: str
#     unit_from_last_period: timedelta
#     unit_from_current_period: timedelta
#     unit_transferred: timedelta


# class INVCE_item_contract_charged(TypedDict):
#     title: str
#     unit_used: str
#     price: float


# class INVCE_item_contract(TypedDict):
#     tax_doc: str
#     free_units: dict[str, INVCE_item_contract_units]
#     service_charged: dict[str, INVCE_item_contract_charged]
#     phone_number: str
#     total_sum: float


# class INVCE_item_header(TypedDict):
#     created: datetime


# class INVCE_item(TypedDict):
#     contracts: dict[str, INVCE_item_contract]
#     header: INVCE_item_header


class Watch:
    def __init__(self, uid: str, pwd: str, detach: bool = False, base_url=URL.LOGIN):
        options = Options()
        self.uid = uid
        self.pwd = pwd
        self.base_url = base_url
        options.add_argument("--headless")
        options.add_experimental_option("detach", detach)

        if os.environ.get("CHROMEDRIVER_PATH"):
            self.driver = webdriver.Chrome(
                executable_path=os.environ.get("CHROMEDRIVER_PATH"),
                chrome_options=options,
            )
        else:
            self.driver = webdriver.Chrome(options=options)

    def to(self, url: str):
        self.driver.get(url)
        return self.driver

    def login(self):
        ins = self.to(self.base_url)
        WebDriverWait(driver=ins, timeout=15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "login-form"))
        )
        login_input = ins.find_element(By.ID, "username")
        login_input.send_keys(self.uid)
        pass_input = ins.find_element(By.ID, "password")
        pass_input.send_keys(self.pwd)
        pass_input.send_keys(Keys.RETURN)
        return self

    def scrape_contracts(self):
        contract_list: List[Contract] = []
        if self.driver.current_url == URL.OVERVIEW:
            list = self.driver.find_elements(By.CLASS_NAME, "dashboard-tile")
            for box in list:
                items = box.find_elements(By.CLASS_NAME, "dashboard-list__item")
                contract: Contract = {
                    "tariff": box.find_element(
                        By.CLASS_NAME, "dashboard-tile__title"
                    ).text,
                    "uuid": items[0]
                    .find_element(By.CLASS_NAME, "dashboard-list__value")
                    .text,
                    "data": items[1]
                    .find_element(By.CLASS_NAME, "dashboard-list__value")
                    .text,
                }
                contract_list.append(contract)
        return contract_list

    def scrape_invoicelist(self):
        instance = self.to(URL.INVOICES)
        invoice_list: List[Invoice] = []
        if self.driver.current_url == URL.INVOICES:
            WebDriverWait(instance, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "docs-table"))
            )
            table = instance.find_element(By.CLASS_NAME, "docs-table")
            invoices = table.find_elements(By.CLASS_NAME, "no-info")
            for inv in invoices:
                cols = inv.find_elements(By.TAG_NAME, "td")
                anchor_ele = (
                    cols[0].find_element(By.TAG_NAME, "a").get_attribute("href")
                )
                status_ele = cols[5].find_element(By.CLASS_NAME, "status")
                status_classes = status_ele.get_attribute("class").split()

                invoice = {
                    "invoice_number": int(anchor_ele.replace(URL.INVOICE_DETAIL_, "")),
                    "title": unidecode(cols[0].text),
                    "href": anchor_ele,
                    "created": datetime.strptime(
                        cols[1].text.replace(" ", ""), "%d.%m.%Y"
                    ),
                    "due_date": datetime.strptime(
                        cols[2].text.replace(" ", ""), "%d.%m.%Y"
                    ),
                    "amount_CZK": float(unidecode(cols[4].text).replace(" Kc", "")),
                    "status": unidecode(
                        cols[5]
                        .text.replace("\nDetail platby", "")
                        .replace("Zaplatit on-line", "")
                    ),
                    "paid": True if "-green" in status_classes else False,
                }
                invoice_list.append(invoice)
        return invoice_list

    def get_invoice_details(self, href: str):
        """scrap invoice details, req.parameter - href"""
        instance = self.to(href)
        WebDriverWait(instance, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "layout-wrapper"))
        )
        invoice_details = {}

        # invoice head

        invoice_head = instance.find_elements(
            By.CSS_SELECTOR, ".invoice-head__dates>li"
        )
        invoice_overview_table = instance.find_element(
            By.CSS_SELECTOR, "table.noBorder.compress-2.inMobCenter.overview-col-2"
        )
        table_rows = invoice_overview_table.find_elements(By.TAG_NAME, "tr")

        created = table_rows[4].find_element(By.CLASS_NAME, "_text-align-right")
        invoice_details["header"] = {
            "created": datetime.strptime(created.text.replace(" ", ""), "%d.%m.%Y"),
        }

        tax_document = invoice_head[1].text.replace("Daňový doklad č.:", "")

        invoice_details["contracts"] = {}

        contracts = instance.find_elements(By.CSS_SELECTOR, ".invoice>table")

        for i, contract in enumerate(contracts):  # sluzba
            sections = contract.find_elements(By.CLASS_NAME, "gray-wrapper")

            item_contract = {}
            item_contract["tax_doc"] = tax_document
            head_dates = contract.find_element(By.CLASS_NAME, "invoice-head__dates")
            item_invoice_phone_number_str = head_dates.find_elements(By.TAG_NAME, "li")[
                1
            ].text
            item_invoice_phone_number = str(
                item_invoice_phone_number_str.replace("Telefonní číslo: ", "")
            )  # telefonni cislo

            free_units = sections[0]  # sekce volne jednotky
            free_units_items = free_units.find_elements(By.TAG_NAME, "tr")[1:]

            item_contract["free_units"] = {}
            for item in free_units_items:
                item_title = unidecode(item.find_elements(By.TAG_NAME, "td")[0].text)
                item_unit_from_last_period = unidecode(
                    item.find_elements(By.TAG_NAME, "td")[1].text
                )

                if ":" in item_unit_from_last_period:
                    last_period_minutes, last_period_seconds = map(
                        int, item_unit_from_last_period.split(":")
                    )
                    unit_from_last_period = timedelta(
                        minutes=last_period_minutes, seconds=last_period_seconds
                    )
                else:
                    try:
                        unit_from_last_period = int(item_unit_from_last_period)
                    except ValueError:
                        if item_unit_from_last_period == 'Neomezene':
                            unit_from_last_period = 'Infinity'
                        else:
                            unit_from_last_period = 0


                item_unit_from_current_period = unidecode(
                    item.find_elements(By.TAG_NAME, "td")[2].text
                )

                if ":" in item_unit_from_current_period:
                    current_period_minutes, current_period_seconds = map(
                        int, item_unit_from_current_period.split(":")
                    )
                    unit_from_current_period = timedelta(
                        minutes=current_period_minutes, seconds=current_period_seconds
                    )
                else:
                    try:
                       unit_from_current_period = int(item_unit_from_current_period)
                    except ValueError:
                        if item_unit_from_current_period == 'Neomezene':
                            unit_from_last_period = 'Infinity'
                        else:
                            unit_from_last_period = 0

                item_unit_transferred = unidecode(
                    item.find_elements(By.TAG_NAME, "td")[3].text
                )

                if ":" in item_unit_transferred:
                    transferred_minutes, transfered_seconds = map(
                        int, item_unit_transferred.split(":")
                    )

                    unit_transferred = timedelta(
                        minutes=transferred_minutes, seconds=transfered_seconds
                    )
                else:
                    unit_transferred = item_unit_transferred

                item_free_unit = {
                    "title": item_title,
                    "unit_from_last_period": unit_from_last_period,
                    "unit_from_current_period": unit_from_current_period,
                    "unit_transferred": unit_transferred,
                }
                item_contract["free_units"][item_free_unit["title"]] = item_free_unit

            regular_fees = sections[1]  # sekce pravidelne poplatky

            charges_services = sections[2]  # sekce poskytovane sluzby
            charges_services_items = charges_services.find_elements(By.TAG_NAME, "tr")[
                2:
            ]

            item_contract["service_charged"] = {}
            for service in charges_services_items:
                children = service.find_elements(By.CSS_SELECTOR, "*")
                if len(children) > 5:
                    service_title = unidecode(
                        service.find_elements(By.TAG_NAME, "td")[0]
                        .text.replace("-", "")
                        .strip()
                    )
                    service_unit_used = unidecode(
                        service.find_elements(By.TAG_NAME, "td")[3].text
                    )
                    service_price = unidecode(
                        service.find_elements(By.TAG_NAME, "td")[4].text
                    )
                    service_item = {
                        "label": service_title,
                        "unit_used": service_unit_used,
                        "price": float(
                            service_price.replace(",", ".").replace(" ", "")
                        ),
                    }
                    item_contract["service_charged"][
                        service_item["label"]
                    ] = service_item

            for index, section in enumerate(sections):
                section_title = section.find_element(By.TAG_NAME, "strong").text
                if section_title == "Ostatní poplatky":
                    item_contract["other_services"] = []
                    for service in sections[index].find_elements(By.TAG_NAME, "tr")[1:]:
                        item_title = service.find_elements(By.TAG_NAME, "td")[0].text
                        item_value = service.find_elements(By.TAG_NAME, "td")[1].text
                        service_item = {
                            "title": item_title,
                            "price": float(
                                item_value.replace(",", ".").replace(" ", "")
                            ),
                        }
                        item_contract["other_services"].append(service_item)

            total_sum_wrap = sections[4]
            item_total_sum = total_sum_wrap.find_element(
                By.CLASS_NAME, "_text-align-right"
            ).text

            item_contract["phone_number"] = item_invoice_phone_number
            invoice_details["contracts"][item_contract["phone_number"]] = item_contract
            invoice_details["contracts"][item_contract["phone_number"]][
                "total_sum"
            ] = float(item_total_sum.replace(",", ".").replace(" ", ""))
        return invoice_details


