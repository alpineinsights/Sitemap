import os
import boto3
import streamlit as st
from botocore.exceptions import NoCredentialsError
import xml.etree.ElementTree as ET


def get_s3_urls(bucket_name, region, prefix=''):
    try:
        s3 = boto3.client('s3',
                          aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                          region_name=region)
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        urls = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    urls.append(f"https://{bucket_name}.s3.{region}.amazonaws.com/{obj['Key']}")
        return urls
    except NoCredentialsError:
        st.error("AWS credentials not found. Please check your environment variables.")
        return []

def create_sitemap(urls):
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    for url in urls:
        url_element = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url_element, "loc")
        loc.text = url

    return ET.ElementTree(urlset)

def write_sitemap_to_s3(bucket_name, region, sitemap_tree):
    s3 = boto3.client('s3',
                      aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                      aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                      region_name=region)
    sitemap_path = "sitemap.xml"
    sitemap_tree.write(sitemap_path, encoding="utf-8", xml_declaration=True)
    s3.upload_file(sitemap_path, bucket_name, "sitemap.xml",
                   ExtraArgs={'ContentType': 'application/xml'})
    st.success(f"Sitemap updated: https://{bucket_name}.s3.{region}.amazonaws.com/sitemap.xml")

def main():
    st.title("S3 Sitemap Generator")
    st.sidebar.header("Settings")
    aws_region = st.sidebar.text_input("AWS Region", value=os.getenv("AWS_REGION"))
    s3_bucket = st.sidebar.text_input("S3 Bucket", value=os.getenv("S3_BUCKET"))
    generate_btn = st.sidebar.button("Generate/Update Sitemap")

    if generate_btn:
        st.info("Retrieving S3 URLs...")
        urls = get_s3_urls(s3_bucket, aws_region)
        if urls:
            st.success(f"Retrieved {len(urls)} URLs from the bucket.")
            sitemap_tree = create_sitemap(urls)
            write_sitemap_to_s3(s3_bucket, aws_region, sitemap_tree)
        else:
            st.error("No URLs found or unable to access the bucket.")

if __name__ == "__main__":
    main()


