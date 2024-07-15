from flask import render_template, request, jsonify, redirect, url_for, send_file, make_response
from flask_app import app, db
from flask_app.models import TestArchive, Tag, TestTag
import csv
import io
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import fitz

# Define colors for each result
result_colors = {
    
    # Hermes
    'PASSED': 'lightgreen',
    'FAILED': '#FF6347',
    'UNSUPPORTED': 'lightgrey',
    'NOT APPLICABLE': 'darkgrey',
    'RESTART DETECTED': 'lightblue',
    'ABORTED': 'orange',
    'REQUIRES REVIEW': 'grey',
    # Ligada
    'Passed': 'lightgreen',
    'Failed': '#FF6347',
    'Error': 'orange',
    'No result': 'lightgrey'
}

plt.rcParams['font.family'] = 'Roboto'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    csv_file = request.files['csv_file']
    if csv_file:
        # Get the filename of the uploaded CSV file
        uploaded_filename = csv_file.filename

        # Process the CSV file
        with io.TextIOWrapper(csv_file, encoding='utf-8', newline='') as text_file:
            reader = csv.reader(text_file, delimiter=',')  # Assuming CSV delimiter is comma (',')
            next(reader)  # Skip the header row
            
            new_rows = []  # To store rows for the new CSV file
            for row in reader:
                test_case_id = row[0]  # Assuming the first column contains the test case ID
                result = row[1]  # Assuming the second column contains the test result

                # Find the corresponding test result in the database
                test_result = TestArchive.query.filter_by(test_case_id=test_case_id).first()
                if test_result:
                    # Fetch associated tags from TestTag table
                    test_tags = TestTag.query.filter_by(test_archive_id=test_result.id).all()
                    if test_tags:
                        # Get tag names associated with the test result
                        tags = [test_tag.tag.tag for test_tag in test_tags]
                    else:
                        tags = ['UNCATEGORISED TAG']  # Add 'UNCATEGORISED TAG' if no tags found
                else:
                    tags = ['UNCATEGORISED']  # Add 'UNCATEGORISED' if test case ID is not found in the database

                # Create a new row with test case ID, result, and tags
                new_row = [test_case_id, result, ', '.join(tags)]
                new_rows.append(new_row)

            # Construct the new filename with the 'tagged_' prefix
            new_filename = 'tagged_' + uploaded_filename
            
            # Write new rows to the new CSV file
            with open(new_filename, 'w', newline='') as new_file:
                writer = csv.writer(new_file)
                writer.writerow(['id', 'results', 'tags'])  # Header
                writer.writerows(new_rows)

            return 'File processed successfully!'
    return 'File uploaded successfully!'

def generate_total_report(csv_filename, project_details):
    # Load data
    data = pd.read_csv(csv_filename)

    # Create figure and subplots for project_table, results_table, and pie chart
    fig, axs = plt.subplots(1, 3, figsize=(14, 7))

    # Plot Project table
    project_table_data = [[label, value] for label, value in project_details.items()]
    cell_colours = [['#01546F', '#4EC1E0'] for _ in project_table_data]
    project_table = axs[0].table(cellText=project_table_data, loc='center', cellLoc='center', colWidths=[0.4, 0.6], edges='closed', cellColours=cell_colours)
    project_table.auto_set_font_size(True)
    project_table.auto_set_column_width([0, 1])
    project_table.set_fontsize(11)
    project_table.scale(2, 2)  # Adjust table size
    for row in range(len(project_table_data)):
        for col in range(len(project_table_data[0])):
            cell = project_table[row, col]
            text_colour = 'white' if col == 0 else 'black'
            cell.set_text_props(color=text_colour, weight='bold' if col == 0 else 'normal')  # Set weight to 'bold' for the first column
            cell.set_edgecolor('#01546F')
    axs[0].axis('off')

    # Calculate result counts and total results
    result_counts = data['results'].value_counts()
    total_results = result_counts.sum()

    # Plot Results table
    results_table_data = [['Verdict', 'Count', 'Percentage']]
    results_table_data.append(['Total', total_results, '100%'])
    results_table_data.extend([[result, count, f'{(count / total_results) * 100:.1f}%'] for result, count in result_counts.items()])
    results_table = axs[1].table(cellText=results_table_data, loc='center', cellLoc='center', colWidths=[0.2, 0.2, 0.2])
    results_table.auto_set_font_size(False)
    results_table.set_fontsize(11) 
    results_table.scale(2, 2) 
    results_table.auto_set_column_width([0, 1, 2])
    for key, cell in results_table.get_celld().items():
        if key[0] == 0:
            cell.set_facecolor('#01546F')
            cell.set_edgecolor('#01546F')
            cell.set_text_props(weight='bold', color='white')
        else:
            cell.set_facecolor('#4EC1E0')
            cell.set_edgecolor('#01546F')
            cell.set_text_props(color='black')
    axs[1].axis('tight')
    axs[1].axis('off')

    # Plot Pie chart
    pie_colors = [result_colors[result] for result in result_counts.index]
    axs[2].pie(result_counts, autopct='%1.1f%%', startangle=140, colors=pie_colors, radius=0.7)
    axs[2].legend(result_counts.index, loc="best", fontsize='small')
    axs[2].set_aspect('equal')
    axs[2].set_xlim(-1.1, 1.1)
    axs[2].set_ylim(-1.1, 1.1)

    # Adjust layout
    plt.subplots_adjust(wspace=0.5)
    fig.tight_layout(rect=[0, 0.03, 1, 0.97])  # Add more space to the top of the page

    # Get the directory path of the Flask application
    app_dir = os.path.dirname(os.path.abspath(__file__))

    # Specify the absolute path of the PDF file in the parent directory
    reports_dir = os.path.join(os.path.dirname(app_dir), 'Reports')
    pdf_filename = os.path.join(reports_dir, 'test_results_summary.pdf')

    # Check if the directory exists, if not, create it
    if not os.path.isdir(reports_dir):
        os.makedirs(reports_dir)

    # Add bar charts
    with PdfPages(pdf_filename) as pdf:
        pdf.savefig(fig)

        # Second figure with horizontal bar charts
        stacked_data = data.groupby('tags')['results'].value_counts().unstack().fillna(0)
        normalized_data = stacked_data.div(stacked_data.sum(axis=1), axis=0) * 100
        colors = [result_colors[result] for result in stacked_data.columns]

        # Calculate the height of the figure dynamically based on the number of tags
        height_per_point = 0.3
        fig_height = height_per_point * len(data['tags'].unique())

        fig2, ax2 = plt.subplots(figsize=(14, fig_height))  # Adjust height based on number of tags

        # Check for the correct spelling of the failed verdict
        verdict = next((col for col in ['FAILED', 'Failed'] if col in normalized_data.columns), 'Failed')

        # Sort the normalized_data DataFrame by the determined verdict column
        normalized_data_sorted = normalized_data.sort_values(by=verdict, ascending=True)

        # Plot the sorted normalized stacked bar chart
        normalized_data_sorted.plot(kind='barh', stacked=True, ax=ax2, color=colors, width=0.8)

        ax2.set_ylabel('Tag')
        ax2.set_xlabel('Percentage')
        ax2.set_title('Tags Normalised Stacked Bar Chart')

        # Add data labels
        for bar in ax2.patches:
            if bar.get_width() != 0:  # Only add labels for non-zero segments
                value = bar.get_width()
                label = f'{value:.1f}%' if value % 1 != 0 else f'{int(value)}%'  # Format label
                ax2.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() / 2 + bar.get_y(),
                        label,
                        ha='center', va='center',
                        color='black', weight='bold', size=10)

        plt.tight_layout()
        pdf.savefig(fig2)  # Second figure with horizontal bar charts

        # Sort the stacked_data DataFrame by the total count of each row
        stacked_data_sorted = stacked_data.sum(axis=1).sort_values(ascending=True)

        # Reindex the stacked_data DataFrame using the sorted index
        stacked_data_sorted = stacked_data.reindex(stacked_data_sorted.index)

        # Plot the sorted stacked bar chart
        fig3, ax3 = plt.subplots(figsize=(14, fig_height))  # Adjust height based on number of tags
        stacked_data_sorted.plot(kind='barh', stacked=True, ax=ax3, color=colors, width=0.8)

        ax3.set_ylabel('Tag')
        ax3.set_xlabel('Count')
        ax3.set_title('Tags Stacked Bar Chart')

        # Add data labels
        for bar in ax3.patches:
            if bar.get_width() != 0:  # Only add labels for non-zero segments
                ax3.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() / 2 + bar.get_y(),
                        f'{bar.get_width():.0f}',  # Format label to integer (no decimal places)
                        ha='center', va='center',
                        color='black', weight='bold', size=10)

        plt.tight_layout()
        pdf.savefig(fig3)  # Third figure with horizontal bar charts

    # Return the filename of the generated PDF
    return pdf_filename


@app.route('/generate_total_pdf', methods=['POST'])
def generate_total_pdf():
    csv_file = request.files['csv_file']
    if csv_file:
        test_plan = request.form['test_plan']
        project = request.form['project']
        platform = request.form['platform']
        serial = request.form['serial']
        model = request.form['model']
        test_suite = request.form['test_suite']

        # Create project details dynamically based on provided fields
        project_details = {}
        if test_plan:
            project_details['Test plan'] = test_plan
        if project:
            project_details['Project'] = project
        if platform:
            project_details['Platform'] = platform
        if serial:
            project_details['Serial'] = serial
        if model:
            project_details['Model'] = model
        if test_suite:
            project_details['Test Suite'] = test_suite

        # Generate the PDF report
        pdf_filename = generate_total_report(csv_file, project_details)

        return send_file(pdf_filename, as_attachment=True)
    return 'No CSV file uploaded!'

@app.route('/insert_logo_pdf', methods=['POST'])
def insert_logo_pdf():

    # Get the current working directory
    app_directory = os.getcwd()

    # Define the paths relative to the current working directory
    REPORT_FOLDER = os.path.join(app_directory, 'Reports')
    LOGO_FOLDER = os.path.join(app_directory, 'Report Logos')
    
    pdf_file = request.files['pdf_file']
    logo_file = request.files['logo_file']

    if pdf_file and logo_file:
        # Save the uploaded files to a temporary location
        pdf_file_path = os.path.join(REPORT_FOLDER, pdf_file.filename)
        logo_file_path = os.path.join(LOGO_FOLDER, logo_file.filename)
        pdf_file.save(pdf_file_path)
        logo_file.save(logo_file_path)

        # Open the PDF document
        doc = fitz.open(pdf_file_path)
        
        # Get the dimensions of the logo image
        image = fitz.open(logo_file_path)
        image_width = image[0].rect.width
        image_height = image[0].rect.height
        
        # Get the first page of the PDF
        first_page = doc[0]
        
        # Get the dimensions of the first page
        page_width = first_page.rect.width
        page_height = first_page.rect.height
        
        # Define the maximum dimensions for the logo
        max_logo_width = page_width // 6  # Adjust as needed
        max_logo_height = page_height // 6  # Adjust as needed


        # Calculate the scaling factor
        scale_factor_width = max_logo_width / image_width
        scale_factor_height = max_logo_height / image_height
        scale_factor = min(scale_factor_width, scale_factor_height)

        # Apply scaling if the logo is too large
        if scale_factor < 1:
            image_width *= scale_factor
            image_height *= scale_factor
        
        x = 10  # 10 is the horizontal margin
        y = 10  # 10 is the vertical margin from the top edge
        
        # Define the rectangle for the image placement
        rect = fitz.Rect(x, y, x + image_width, y + image_height)
        
        # Insert the image onto the first page
        first_page.insert_image(rect, filename=logo_file_path)
        
        # Save the modified PDF
        output_pdf_path = 'output_pdf_with_logo.pdf'  # Specify the path to save the output PDF
        doc.save(output_pdf_path)
        
        # Close the PDF documents
        doc.close()
        image.close()

        # Optionally, return the path to the output PDF file
        return f'PDF file with logo inserted: {output_pdf_path}'

    return 'PDF file and logo file are required!'

def generate_tags_report(csv_filename): 

    # Load data
    data = pd.read_csv(csv_filename)
    # Get the unique tags
    tags = sorted(data['tags'].unique())
    # Create a PDF to store all the figures
    pdf_filename = 'tag_summary.pdf'
    with PdfPages(pdf_filename) as pdf:
        for i in range(0, len(tags), 4):

            # Create a figure with 4 subplots arranged vertically for each set of tags
            fig, axs = plt.subplots(4, 2, figsize=(14, 18))

            # Iterate over each set of 4 tags
            for j, tag in enumerate(tags[i:i+4]):
                # Filter the data for the current tag
                tag_data = data[data['tags'] == tag]
                
                # Count the occurrences of each result for the current tag
                result_counts = tag_data['results'].value_counts()
                
                # Calculate percentages
                total_results = result_counts.sum()
                percentages = [(count / total_results) * 100 for count in result_counts]
                
                # Breakdown table for the current tag
                axs[j, 0].axis('tight')
                axs[j, 0].axis('off')

                # Prepare data for the table dynamically for the current tag
                table_data = [['Verdict', 'Count', 'Percentage']]
                table_data.append(['Total', total_results, ''])
                for result, count, percentage in zip(result_counts.index, result_counts, percentages):
                    table_data.append([result, count, f'{percentage:.1f}%'])

                # Set font properties
                plt.rcParams['font.family'] = 'roboto'

                # Create the table
                table = axs[j, 0].table(cellText=table_data, loc='center', cellLoc='center', colWidths=[0.18, 0.08, 0.12])
                
                # Style the table
                table.auto_set_font_size(False)
                # Set background color and font color for header row
                header_cells = table.get_celld()
                for key in header_cells:
                    if key[0] == 0:  # Identifying the header row by its position (typically the first row)
                        header_cells[key].set_facecolor('gray')
                        header_cells[key].set_edgecolor('gray')
                        header_cells[key].set_text_props(weight='bold', color='white')

                # Iterate over the cells (excluding header row) and set the background color individually
                colors = ['lightgray', 'lightgray']
                for key, cell in header_cells.items():
                    if key[0] != 0:  # Exclude the header row
                        cell.set_facecolor(colors[0])
                        cell.set_edgecolor('gray')

                # Pie chart for the current tag
                pie_colors = [result_colors[result] for result in result_counts.index]
                pie = axs[j, 1].pie(result_counts, autopct='%1.1f%%', startangle=140, colors=pie_colors, radius=0.5)
                legend_labels = result_counts.index
                axs[j, 1].legend(pie[0], legend_labels, loc="center left", bbox_to_anchor=(1, 0.5))

                # Adjust the size of the pie chart
                axs[j, 1].set_aspect('equal')  # Ensure pie chart is circular
                axs[j, 1].set_xlim(-0.9, 0.9)  # Adjust the x-axis limits to change the width of the pie chart
                axs[j, 1].set_ylim(-0.9, 0.9)  # Adjust the y-axis limits to change the height of the pie chart

                 # Add a title for the current tag
                title_text = f"{tag}"
                axs[j, 0].set_title(title_text, loc='center', fontsize=12)

                # Adjust the position of the title between the table and the pie chart
                axs[j, 0].title.set_position([0.85, 0.5])

            # Use tight_layout to adjust the spacing
            fig.tight_layout(rect=[0, 0.03, 1, 0.97])  # Add more space to the top of the page

            # Adjust spacing between subplots
            plt.subplots_adjust(hspace=0.1, wspace=-0.3)  # Increase the hspace value for wider distribution

             # Get the directory path of the Flask application
            app_dir = os.path.dirname(os.path.abspath(__file__))

            # Specify the absolute path of the PDF file in the parent directory
            pdf_filename = os.path.join(os.path.dirname(app_dir), 'tag_summary.pdf')

            # Save the figure with all plots into the PDF file
            pdf.savefig(fig)
            plt.close(fig)
            
    return pdf_filename

@app.route('/generate_tags_pdf', methods=['POST'])
def generate_tags_pdf():
    csv_file = request.files['csv_file']
    if csv_file:
        pdf_filename = generate_tags_report(csv_file)
        return send_file(pdf_filename, as_attachment=True)
    return 'No CSV file uploaded!'
