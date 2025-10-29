import definitions
import glob
import os


def rename_papers():
    """
    Finds all PDF files in the directory specified by `definitions.paper_path`,
    renames them to a sequential integer format (e.g., 0.pdf, 1.pdf).
    """

    paper_list = glob.glob(str(definitions.paper_path) + "/*.pdf")  # get the list of pdfs
    counter = 0

    for paper_name in paper_list:  # iterate through pdfs
        os.rename(paper_name, str(definitions.paper_path) + "/" + str(counter) + ".pdf")  # rename the file
        counter += 1


rename_papers()