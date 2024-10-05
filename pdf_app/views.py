from django.shortcuts import render
from django.http import HttpResponse, FileResponse
import PyPDF2
import io
import fitz
import pdfplumber
import zipfile
import tempfile
from pdf2docx import Converter

def pdf_manager(request):
    if request.method == 'POST':
        operation = request.POST.get('operation')
        uploaded_files = request.FILES.getlist('pdf_files')
        output_file_name = request.POST.get('output_file_name', 'output.pdf')
        outputdocx_name = 'DEFAULT'#request.POST.get('output_file_name', 'output.docx')
        outputdocx_name = request.POST.get('output_file_name', 'output.docx')
        if outputdocx_name == '':
            outputdocx_name = 'Default'
        pdf_paths = []
        for uploaded_file in uploaded_files:
            pdf_paths.append(uploaded_file)

        output_buffer = io.BytesIO()

        match operation:
            case 'merge':
                merge_pdfs_helper(pdf_paths, output_buffer)
                response = FileResponse(output_buffer, as_attachment=True, filename=f'{output_file_name}.pdf')

            case 'split':
                zip_buffer = io.BytesIO()
                split_pdfs_helper(pdf_paths[0], zip_buffer)
                response = FileResponse(zip_buffer, as_attachment=True, filename='split_output.zip')

            case 'extract_text':
                extract_text_helper(pdf_paths[0], output_buffer)
                response = FileResponse(output_buffer, as_attachment=True, filename='extracted_text.txt')

            case 'extract_images':
                zip_buffer = io.BytesIO()
                extract_images_helper(pdf_paths[0], zip_buffer)
                response = FileResponse(zip_buffer, as_attachment=True, filename='extracted_images.zip')

            case 'encrypt':
                password = request.POST.get('password')
                encrypt_pdf_helper(pdf_paths[0], output_buffer, password)
                response = FileResponse(output_buffer, as_attachment=True, filename=f'{output_file_name}.pdf')

            case 'decrypt':
                password = request.POST.get('password')
                decrypt_pdf_helper(pdf_paths[0], output_buffer, password)
                response = FileResponse(output_buffer, as_attachment=True, filename=f'{output_file_name}.pdf')

            case 'rearrange_pages':
                page_order = list(map(int, request.POST.get('page_order').split()))
                rearrange_pages_helper(pdf_paths[0], output_buffer, page_order)
                response = FileResponse(output_buffer, as_attachment=True, filename=f'{output_file_name}.pdf')

            case 'rotate_pages':
                rotation = int(request.POST.get('rotation'))
                rotate_pages_helper(pdf_paths[0], output_buffer, rotation)
                response = FileResponse(output_buffer, as_attachment=True, filename=f'{output_file_name}.pdf')

            case 'read_metadata':
                metadata = read_metadata_helper(pdf_paths[0])
                response = HttpResponse(metadata, content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="metadata.txt"'

            case 'add_metadata':
                title = request.POST.get('title')
                author = request.POST.get('author')
                add_metadata_helper(pdf_paths[0], output_buffer, title, author)
                response = FileResponse(output_buffer, as_attachment=True, filename=f'{output_file_name}.pdf')

            case 'optimize':
                compress_pdf_helper(pdf_paths[0], output_buffer)
                output_buffer.seek(0)  # Reset buffer position
                response = FileResponse(output_buffer, as_attachment=True, filename=f"compressed_{output_file_name}.pdf")
                
            case 'pdf_to_word':
                pdf_to_word_helper(pdf_paths[0], output_buffer)
                output_buffer.seek(0)  # Reset buffer position
                response = FileResponse(output_buffer, as_attachment=True, filename=f"{outputdocx_name}.docx")

        return response

    return render(request, 'pdf_manager.html')

def merge_pdfs_helper(pdf_list, output_buffer):
    pdf_writer = PyPDF2.PdfWriter()
    for pdf in pdf_list:
        pdf_reader = PyPDF2.PdfReader(pdf)
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)

def split_pdfs_helper(pdf_path, zip_buffer):
    pdf_reader = PyPDF2.PdfReader(pdf_path)
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_num])
            page_buffer = io.BytesIO()
            pdf_writer.write(page_buffer)
            page_buffer.seek(0)
            zf.writestr(f"page_{page_num + 1}.pdf", page_buffer.getvalue())
    zip_buffer.seek(0)

def extract_text_helper(pdf_path, output_buffer):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
    output_buffer.write(full_text.encode())
    output_buffer.seek(0)

def extract_images_helper(pdf_path, zip_buffer):
    doc = fitz.open(pdf_path)
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for page_num in range(len(doc)):
            for img_index, img in enumerate(doc.get_page_images(page_num)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                zf.writestr(f"image_p{page_num + 1}_{img_index + 1}.{base_image['ext']}", image_bytes)
    zip_buffer.seek(0)

def encrypt_pdf_helper(input_pdf, output_buffer, password):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_writer = PyPDF2.PdfWriter()
    for page in pdf_reader.pages:
        pdf_writer.add_page(page)
    pdf_writer.encrypt(password)
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)

def decrypt_pdf_helper(input_pdf, output_buffer, password):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_reader.decrypt(password)
    pdf_writer = PyPDF2.PdfWriter()
    for page in pdf_reader.pages:
        pdf_writer.add_page(page)
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)

def rearrange_pages_helper(input_pdf, output_buffer, page_order):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_writer = PyPDF2.PdfWriter()
    for page_num in page_order:
        pdf_writer.add_page(pdf_reader.pages[page_num - 1])
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)

def rotate_pages_helper(input_pdf, output_buffer, rotation):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_writer = PyPDF2.PdfWriter()
    for page in pdf_reader.pages:
        page.rotate(rotation)
        pdf_writer.add_page(page)
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)

def read_metadata_helper(input_pdf):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    metadata = pdf_reader.metadata
    return '\n'.join(f"{key}: {value}" for key, value in metadata.items())

def add_metadata_helper(input_pdf, output_buffer, title, author):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_writer = PyPDF2.PdfWriter()
    for page in pdf_reader.pages:
        pdf_writer.add_page(page)
    pdf_writer.add_metadata({
        '/Title': title,
        '/Author': author
    })
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)
def compress_pdf_helper(input_pdf, output_buffer):
    # Use fitz (PyMuPDF) to open the PDF from the uploaded file object
    doc = fitz.open(stream=input_pdf.read(), filetype="pdf")  # Read from the uploaded file object

    # Iterate through each page and compress images
    for page in doc:
        for img_index in range(len(page.get_images(full=True))):
            xref = page.get_images(full=True)[img_index][0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Here you can implement your image compression logic if needed
            # For now, we will just replace it with the same image
            page.insert_image(page.rect, stream=image_bytes)

    # Save the compressed PDF to the output buffer
    doc.save(output_buffer, garbage=4)
    output_buffer.seek(0)

def pdf_to_word_helper(pdf_file, output_buffer):
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
        temp_pdf.write(pdf_file.read())
        temp_pdf.flush()

        # Use pdf2docx to convert PDF to DOCX
        output_path = temp_pdf.name.replace('.pdf', '.docx')
        cv = Converter(temp_pdf.name)
        cv.convert(output_path, start=0, end=None)
        cv.close()

        # Read the DOCX file and write it to the output buffer
        with open(output_path, 'rb') as docx_file:
            output_buffer.write(docx_file.read())
        output_buffer.seek(0)  # Reset buffer after writing