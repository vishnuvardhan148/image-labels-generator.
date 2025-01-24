import boto3
import os
from PIL import Image, ImageDraw, ImageFont
from botocore.exceptions import NoCredentialsError

# Function to detect labels using Amazon Rekognition
def detect_labels(image_name, bucket_name):
    # Initialize Rekognition client
    rekognition_client = boto3.client('rekognition')

    try:
        # Call Rekognition to detect labels in the image stored in S3
        response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_name}},
            MaxLabels=10,  # Max labels to return
            MinConfidence=75  # Minimum confidence score for labels
        )

        print(f"\nLabels for {image_name}:")
        labels = []
        for label in response['Labels']:
            labels.append(f"{label['Name']}: {label['Confidence']:.2f}%")
            print(f"{label['Name']}: {label['Confidence']:.2f}%")

        # After detecting labels, add them to the image with bounding boxes
        add_labels_to_image(image_name, labels, bucket_name, response)

    except NoCredentialsError:
        print("Credentials not available")

# Function to add labels and bounding boxes onto the image
def add_labels_to_image(image_name, labels, bucket_name, response):
    s3_client = boto3.client('s3')

    try:
        # Download the image from S3 to local storage
        s3_client.download_file(bucket_name, image_name, image_name)

        # Open the image using Pillow
        image = Image.open(image_name)
        draw = ImageDraw.Draw(image)

        # Load a larger font (you can adjust the size or path if necessary)
        font_size = 50  # Set a large font size (you can adjust this)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)  # Change font size here
        except IOError:
            font = ImageFont.load_default()

        # Draw the labels and bounding boxes on the image
        for label in response['Labels']:
            for instance in label.get('Instances', []):
                # Draw bounding boxes around detected objects (if any)
                if 'BoundingBox' in instance:
                    box = instance['BoundingBox']
                    left = box['Left'] * image.width
                    top = box['Top'] * image.height
                    right = (box['Left'] + box['Width']) * image.width
                    bottom = (box['Top'] + box['Height']) * image.height
                    draw.rectangle([left, top, right, bottom], outline="red", width=5)

                    # Annotate the label inside the box with a larger font
                    label_text = label['Name']  # Add other details like temperature if available
                    draw.text((left, top - font_size), label_text, font=font, fill="white")

        # Save the image with labels (Only save the modified image)
        output_image_name = f"labeled_{image_name}"
        image.save(output_image_name)  # This saves the image only after modifications

        print(f"Labeled image saved as {output_image_name}")

    except NoCredentialsError:
        print("Credentials not available")

# Main function to process images from the S3 bucket
def main():
    bucket_name = 'my-image-labels-bucket'  # Change this to your S3 bucket name

    # Create an S3 client
    s3_client = boto3.client('s3')

    try:
        # List all the objects (images) in the S3 bucket
        objects = s3_client.list_objects_v2(Bucket=bucket_name)

        # Check if the bucket contains any objects
        if 'Contents' not in objects:
            print("No images found in the bucket.")
            return

        # Loop through each object (image) in the bucket
        for obj in objects['Contents']:
            image_name = obj['Key']  # Get the image name (file key)

            # Process each image if it's an image file (jpg, jpeg, png)
            if image_name.lower().endswith(('jpg', 'jpeg', 'png')):
                detect_labels(image_name, bucket_name)

    except NoCredentialsError:
        print("Credentials not available")

# Run the main function
if __name__ == "__main__":
    main()
