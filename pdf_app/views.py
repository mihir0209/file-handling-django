from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
import PyPDF2
import os
import fitz
import pdfplumber

def pdf_manager(request):
    if request.method == 'POST':
        # Get the selected operation from the dropdown
        operation = request.POST.get('operation')

        # Handle file upload
        uploaded_files = request.FILES.getlist('pdf_files')
        output_file_name = request.POST.get('output_file_name', 'output.pdf')

        # Save uploaded files
        fs = FileSystemStorage()
        pdf_paths = []
        for uploaded_file in uploaded_files:
            filename = fs.save(uploaded_file.name, uploaded_file)
            pdf_paths.append(os.path.join(fs.location, filename))

        # Initialize output path
        output_path = ""

        # Perform action based on operation selection
        match operation:
            case 'merge':
                output_path = os.path.join(fs.location, output_file_name)
                merge_pdfs_helper(pdf_paths, output_path)

            case 'split':
                output_dir = os.path.join(fs.location, "split_output")
                split_pdfs_helper(pdf_paths[0], output_dir)

            case 'extract_text':
                output_text_path = os.path.join(fs.location, "extracted_text.txt")
                extract_text_helper(pdf_paths[0], output_text_path)
                with open(output_text_path, 'r') as f:
                    response = HttpResponse(f.read(), content_type='text/plain')
                    response['Content-Disposition'] = f'attachment; filename="extracted_text.txt"'
                    return response

            case 'extract_images':
                output_images_path = os.path.join(fs.location, "extracted_images")
                extract_images_helper(pdf_paths[0], output_images_path)

            case 'encrypt':
                password = request.POST.get('password')
                output_path = os.path.join(fs.location, output_file_name)
                encrypt_pdf_helper(pdf_paths[0], output_path, password)

            case 'decrypt':
                password = request.POST.get('password')
                output_path = os.path.join(fs.location, output_file_name)
                decrypt_pdf_helper(pdf_paths[0], output_path, password)

            case 'rearrange_pages':
                page_order = list(map(int, request.POST.get('page_order').split()))
                output_path = os.path.join(fs.location, output_file_name)
                rearrange_pages_helper(pdf_paths[0], output_path, page_order)

            case 'rotate_pages':
                rotation = int(request.POST.get('rotation'))
                output_path = os.path.join(fs.location, output_file_name)
                rotate_pages_helper(pdf_paths[0], output_path, rotation)

            case 'read_metadata':
                
                return HttpResponse(read_metadata_helper(pdf_paths[0]))

            case 'add_metadata':
                title = request.POST.get('title')
                author = request.POST.get('author')
                output_path = os.path.join(fs.location, output_file_name)
                add_metadata_helper(pdf_paths[0], output_path, title, author)

            case 'optimize':
                output_path = os.path.join(fs.location, output_file_name)
                optimize_pdf_helper(pdf_paths[0], output_path)

        # Prepare file for download if applicable
        if os.path.exists(output_path):
            with open(output_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{output_file_name}"'
                return response

    return render(request, 'pdf_manager.html')

def merge_pdfs_helper(pdf_list, output_path):
    pdf_writer = PyPDF2.PdfWriter()
    for pdf in pdf_list:
        pdf_reader = PyPDF2.PdfReader(pdf)
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
    with open(output_path, 'wb') as out:
        pdf_writer.write(out)

def split_pdfs_helper(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdf_reader = PyPDF2.PdfReader(pdf_path)
    for page_num in range(len(pdf_reader.pages)):
        pdf_writer = PyPDF2.PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[page_num])
        output_path = os.path.join(output_dir, f"page_{page_num + 1}.pdf")
        with open(output_path, 'wb') as out:
            pdf_writer.write(out)

def extract_text_helper(pdf_path, output_text_path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
    with open(output_text_path, 'w') as out:
        out.write(full_text)

def extract_images_helper(pdf_path, output_images_path):
    os.makedirs(output_images_path, exist_ok=True)
    doc = fitz.open(pdf_path)
    for page in range(len(doc)):
        images = doc.load_page(page).get_images(full=True)
        for img_index, image in enumerate(images):
            xref = image[0]
            base_image = doc.extract_image(xref)
            image_filename = os.path.join(output_images_path, f"image_{page + 1}_{img_index + 1}.{base_image['ext']}")
            with open(image_filename, "wb") as f:
                f.write(base_image["image"])

def encrypt_pdf_helper(input_pdf, output_pdf, password):
    pdf_writer = PyPDF2.PdfWriter()
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    for page_num in range(len(pdf_reader.pages)):
        pdf_writer.add_page(pdf_reader.pages[page_num])
    pdf_writer.encrypt(user_pwd=password, use_128bit=True)
    with open(output_pdf, 'wb') as out:
        pdf_writer.write(out)

def decrypt_pdf_helper(input_pdf, output_pdf, password):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_reader.decrypt(password)
    pdf_writer = PyPDF2.PdfWriter()
    for page_num in range(len(pdf_reader.pages)):
        pdf_writer.add_page(pdf_reader.pages[page_num])
    with open(output_pdf, 'wb') as out:
        pdf_writer.write(out)

def rearrange_pages_helper(input_pdf, output_pdf, page_order):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_writer = PyPDF2.PdfWriter()
    for page_num in page_order:
        pdf_writer.add_page(pdf_reader.pages[page_num])
    with open(output_pdf, 'wb') as out:
        pdf_writer.write(out)

def rotate_pages_helper(input_pdf, output_pdf, rotation):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_writer = PyPDF2.PdfWriter()
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        page.rotate(rotation)
        pdf_writer.add_page(page)
    with open(output_pdf, 'wb') as out:
        pdf_writer.write(out)

def read_metadata_helper(input_pdf):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    metadata = pdf_reader.metadata
    response_content = "<html><body>"
    response_content += "<h1>PDF Metadata</h1>"
    response_content += "<ul>"
    
    for key, value in metadata.items():
        response_content += f"<li><strong>{key}:</strong> {value}</li>"
    
    response_content += "</ul>"
    response_content += "</body></html>"
    
    # Return metadata as an HTML response
    return HttpResponse(response_content, content_type='text/html')
    
def add_metadata_helper(input_pdf, output_pdf, title, author):
    pdf_reader = PyPDF2.PdfReader(input_pdf)
    pdf_writer = PyPDF2.PdfWriter()
    for page_num in range(len(pdf_reader.pages)):
        pdf_writer.add_page(pdf_reader.pages[page_num])
    pdf_writer.add_metadata({'/Title': title, '/Author': author})
    with open(output_pdf, 'wb') as out:
        pdf_writer.write(out)

def optimize_pdf_helper(input_file, output_file):
    pdf = fitz.open(input_file)
    pdf.save(output_file, garbage=3, deflate=True)
