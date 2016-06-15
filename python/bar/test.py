"""
The MIT License (MIT)

Copyright (c) 2016 Jake Lussier (Stanford University)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import sys, os, argparse, select, json, urllib2, cv2
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from utils.general_utils import *
from barcode.barcode_reader import *
from fridge import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Stream RFID data.')
    #parser.add_argument("--data", help="Input directory")
    args = parser.parse_args()
    
    reader = BarcodeReader()
    product_data = json.loads(open(PRODUCT_DATA).read()) if os.path.exists(PRODUCT_DATA) else {}
    while True:
        barcode = reader.read()
        if barcode:
            print barcode
            if barcode.code in product_data:
                code_data = product_data[barcode.code]
            else:
                code_data = json.loads(urllib2.urlopen(EAN_URL % barcode.code).read())
                product_data[barcode.code] = code_data
                json.dump(product_data, open(PRODUCT_DATA,"w"), \
                          sort_keys=True, indent=2, separators=(',', ': '))
            ean_im_url = code_data["product"]["image"]
            ean_im_path = ean_im_url.replace("http://eandata.com/image/products", PRODUCT_IMGS)
            print PRODUCT_IMGS
            print ean_im_path
            ims_dir = os.path.dirname(ean_im_path)
            # Create ims dir if does not yet exist.
            if not os.path.exists(ims_dir): os.makedirs(ims_dir)
            # Download ean image if does not yet exist.
            if not os.path.exists(ean_im_path):
                r = urllib2.Request(ean_im_url)
                try:
                    open(ean_im_path, "w").write(urllib2.urlopen(r, timeout=5.0).read())
                except urllib2.URLError as e:
                    logging.warning("Warning '%s' for url %s" % (str(e), im_url))
                    continue
            # Display any/all images.
            if os.path.exists(ean_im_path):
                cv2.imshow("vis", resize(cv2.imread(ean_im_path), 4.0))
        if getKey(cv2.waitKey(100))=='q': break
    reader.disconnect()
