from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, FileResponse
import PyPDF2
import os
import fitz
import pdfplumber
import zipfile
import io

def pdf_manager(request):
    if request.method == 'POST':
        operation = request.POST.get('operation')
        uploaded_files = request.FILES.getlist('pdf_files')
        output_file_name = request.POST.get('output_file_name', 'output.pdf')

        fs = FileSystemStorage()
        pdf_paths = []
        for uploaded_file in uploaded_files:
            filename = fs.save(uploaded_file.name, uploaded_file)
            pdf_paths.append(os.path.join(fs.location, filename))

        output_buffer = io.BytesIO()

        match operation:
            case 'merge':
                merge_pdfs_helper(pdf_paths, output_buffer)
                response = FileResponse(output_buffer, as_attachment=True, filename=output_file_name)

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
                response = FileResponse(output_buffer, as_attachment=True, filename=output_file_name)

            case 'decrypt':
                password = request.POST.get('password')
                decrypt_pdf_helper(pdf_paths[0], output_buffer, password)
                response = FileResponse(output_buffer, as_attachment=True, filename=output_file_name)

            case 'rearrange_pages':
                page_order = list(map(int, request.POST.get('page_order').split()))
                rearrange_pages_helper(pdf_paths[0], output_buffer, page_order)
                response = FileResponse(output_buffer, as_attachment=True, filename=output_file_name)

            case 'rotate_pages':
                rotation = int(request.POST.get('rotation'))
                rotate_pages_helper(pdf_paths[0], output_buffer, rotation)
                response = FileResponse(output_buffer, as_attachment=True, filename=output_file_name)

            case 'read_metadata':
                metadata = read_metadata_helper(pdf_paths[0])
                response = HttpResponse(metadata, content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="metadata.txt"'

            case 'add_metadata':
                title = request.POST.get('title')
                author = request.POST.get('author')
                add_metadata_helper(pdf_paths[0], output_buffer, title, author)
                response = FileResponse(output_buffer, as_attachment=True, filename=output_file_name)

            case 'optimize':
                optimize_pdf_helper(pdf_paths[0], output_buffer)
                response = FileResponse(output_buffer, as_attachment=True, filename=output_file_name)

        # Clean up temporary files
        for pdf_path in pdf_paths:
            os.remove(pdf_path)

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

def optimize_pdf_helper(input_pdf, output_buffer):
    doc = fitz.open(input_pdf)
    doc.save(output_buffer, garbage=4, deflate=True, clean=True)
    output_buffer.seek(0)