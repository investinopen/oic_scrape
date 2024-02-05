import scrapy
import re
from oic_scrape.items import GrantItem
from datetime import datetime


class SloanSpider(scrapy.Spider):
    source_name = "sloan.org"
    source_type = "grants"
    name = f"{source_name}_{source_type}"
    # start_urls = ["https://sloan.org/grants-database?page=1"]

    def start_requests(self):
         url = "https://sloan.org/grants-database?page=1"
         yield scrapy.Request(url, meta={'playwright': True})

    def parse(self, response):
        for grant in response.xpath(
            "//div[@class='database-grants']/ul[@class='data-list']/li"
        ):
            permalink_rel = grant.css("a.permalink::attr(href)").get()
            grant_id = re.search("/grant-detail/(.*)", permalink_rel).group(1)

            # Get the weird things that are hard to extract
            kv = {"Sub-program": None, "Program": None, "Investigator": None}
            for label in grant.css("ul.col li"):
                k = label.css("span.label::text").get().strip()
                v = label.css("li").re("</span>\s*(.*)\s*</li>")[0]
                kv[k] = v
                

            program_of_funder = (
                f"{kv['Program']} > {kv['Sub-program']}"
                if kv["Sub-program"]
                else kv["Program"]
            )

            yield GrantItem(
                grant_id=f"{self.source_name}:{self.source_type}:{grant_id}",
                funder_name="Alfred P. Sloan Foundation",
                funder_ror_id="https://ror.org/052csg198",
                recipient_org_name=grant.css("div.grantee").re(r"</span>(.*)\n\t</div>")[0],
                OI=None,
                pi_name=kv["Investigator"],
                grant_year=grant.css("div.year").re(r"</span>(.*)\n\t</div>")[0],
                award_amount=grant.css("div.amount").re(r"</span>(.*)\n\t</div>")[0],
                award_currency="USD",  # Assuming the currency is USD
                award_amount_usd=grant.css("div.amount").re(r"</span>(.*)\n\t</div>")[0],
                source="sloan.org",
                grant_description=grant.css("div.brief-description > p::text").get(),
                program_of_funder=program_of_funder,
                _crawled_at = datetime.utcnow(),
            )

        next_page = response.css("a.pager-right::attr(href)").get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)