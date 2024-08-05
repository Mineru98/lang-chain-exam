import os

import fire
import fitz


# PDF를 PNG로 변환
def pdf_to_png(pdf_path: str, output_folder: str = "output"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # PDF 문서를 열기
    pdf_document = fitz.open(pdf_path)

    # 각 페이지를 이미지로 변환
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()

        # 이미지 파일 이름 생성
        page_filename = os.path.join(output_folder, f"page_{page_num + 1}.png")

        # PNG 파일로 저장
        pix.save(page_filename)
        print(f"Saved {page_filename}")


class PdfConvertAgent:
    def run(self, file: str):
        pdf_to_png(file)


if __name__ == "__main__":
    fire.Fire(PdfConvertAgent)
