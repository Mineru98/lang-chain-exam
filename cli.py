import fire

from github_summary_agent.index import GithubSummaryAgent
from pdf_loader_agent.index import PdfSummaryAgent
from url_summary_agent.index import UrlSummaryAgent
from youtube_summary_agent.index import YoutubeSummaryAgent


class Main:
    def github(self, **kwargs):
        agent = GithubSummaryAgent()
        agent.run(**kwargs)

    def pdf(self, **kwargs):
        agent = PdfSummaryAgent()
        agent.run(**kwargs)

    def url(self, **kwargs):
        agent = UrlSummaryAgent()
        agent.run(**kwargs)

    def youtube(self, **kwargs):
        agent = YoutubeSummaryAgent()
        agent.run(**kwargs)


if __name__ == "__main__":
    fire.Fire(Main)
