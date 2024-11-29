from .models import Barcode

def generate_barcode_images(start=1000, count=50):
    """
    Generate sequential barcodes in the format 'iSANSXXXX' and save them to the database.
    
    Args:
        start (int): The starting number for the barcode sequence.
        count (int): The number of barcodes to generate.
    """
    for i in range(count):
        barcode_value = f"iSANS{start + i}"  # Sequential barcode in the format iSANSXXXX
        
        # Save barcode to the database with status 'unused'
        barcode_instance = Barcode(
            code=barcode_value,
            status='unused'  # Set status to 'unused'
        )
        barcode_instance.save()

        print(f"Generated and saved barcode: {barcode_value}")