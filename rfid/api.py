#created
from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.utils import flt, getdate, datetime
from erpnext.stock.utils import get_latest_stock_qty
import json
from frappe import _, throw, msgprint, utils
from frappe.utils import cint, flt, cstr, comma_or, getdate, add_days, getdate, rounded, date_diff, money_in_words

#CONSTANTS

RFID_DOC_DETAILS_LABEL = "RFID Tag Info" #DOCTYPE NAME TO MANINTAIN ALL RFID TRANSCATIONS
RFID_DOC_DETAILS_CHILD_LABEL = "RFID Tag Association Info" #CHILD DOC OF RFID_DOC_DETAILS
RFID_DOC_DETAILS_CHILD_NAME = "rfid_tag_association_info"

#git


@frappe.whitelist()
def hellosub(loggedInUser):
	return 'pong'

@frappe.whitelist()
def frappe_db_talk_check():
	#checking
	permitted_doctypes = frappe.db.sql("""select permitted_doctype from `tab+RFID_PERMITTED_DOCTYPES_LABEL+`""",as_dict=1)
	return permitted_doctypes

@frappe.whitelist()
def get_permitted_doctype_data():
	permitted_doctypes = frappe.db.sql("""select permitted_doctype,number_of_rfid_tags_per_record from `tabPermitted DocTypes for RFID Association`""",as_dict=1)
	return permitted_doctypes

#associate_doctype_rfid_tags()
@frappe.whitelist()
def associate_doctype_rfid_tags(doc_type , doc_no,scanned_rfid_tag_data):
	scanned_rfid_tag_data = json.loads(scanned_rfid_tag_data)
	doc_to_be_update = frappe.get_doc(doc_type ,doc_no)
	for tag_position in scanned_rfid_tag_data:
		doc_to_be_update.db_set(tag_position, scanned_rfid_tag_data[tag_position])
		doc_to_be_update.save()

	updated_doc = frappe.get_doc(doc_type ,doc_no)
	is_updated = 1
	for tag_position in scanned_rfid_tag_data: #validation loop
		none_check = getattr(updated_doc,tag_position)
		if none_check == None  and  scanned_rfid_tag_data[tag_position] == " "  :
			pass
		elif scanned_rfid_tag_data[tag_position] != getattr(updated_doc,tag_position) :
			is_updated = 0
			break
		else:
			pass

		if scanned_rfid_tag_data[tag_position] == getattr(updated_doc,tag_position) : #debugging
			pass
	return is_updated

#small change for git hub

@frappe.whitelist()
def sample_update():
	#print "***** Enters Sample update scanned_rfid_tag_data",scanned_rfid_tag_data
	rfid_tag_details_doc = frappe.get_doc( "Item", "Vehicle")
	fetch_data = getattr(rfid_tag_details_doc,"item_code")
	return fetch_data

@frappe.whitelist()
def update_rfid_tag_details_child_doc( doc_type,doc_no,matched_rfid_tag_details_name,rfid_tag_position ):
	is_child_doc_updation_complete = 0
	rfid_tag_details_doc = frappe.get_doc( RFID_DOC_DETAILS_LABEL,matched_rfid_tag_details_name )
	is_last_row_ed_updated = False
	last_row_idx = 0 	# lastrowlinearlayout_pointer
	for roww in getattr(rfid_tag_details_doc,RFID_DOC_DETAILS_CHILD_NAME):
		last_row_idx = last_row_idx +1

	for roww in getattr(rfid_tag_details_doc,RFID_DOC_DETAILS_CHILD_NAME):
		if roww.idx == last_row_idx:
			roww.pch_rfid_association_end_date = utils.now()
			rfid_tag_details_doc.save()
			is_last_row_ed_updated = True

	if is_last_row_ed_updated == True:
		row = rfid_tag_details_doc.append(RFID_DOC_DETAILS_CHILD_NAME,{})
		row.pch_rfid_association_start_date = utils.now()
		row.tag_association = rfid_tag_position
		row.pch_rfid_docid_associated_with = doc_no
		row.pch_rfid_doctype_associated_with = doc_type
		row.idx = last_row_idx+1  #new rows
		rfid_tag_details_doc.save()
		is_child_doc_updation_complete = 1
	return is_child_doc_updation_complete

@frappe.whitelist()
def	create_rfid_tag_details_doc( scanned_rfid_tag_data,tag_association,pch_rfid_docid_associated_with,pch_rfid_doctype_associated_with):

      rfid_child_doc_json = " "
      rfid_doc_json = {
      "doctype": RFID_DOC_DETAILS_LABEL,
      "rfid_tag": scanned_rfid_tag_data,
      RFID_DOC_DETAILS_CHILD_NAME: []
      }

      rfid_child_doc_json ={
      "doctype": RFID_DOC_DETAILS_CHILD_LABEL,
      "tag_association": tag_association,
      "pch_rfid_docid_associated_with": pch_rfid_docid_associated_with,
      "pch_rfid_doctype_associated_with": pch_rfid_doctype_associated_with ,
      "idx":1
      }
      rfid_doc_json[RFID_DOC_DETAILS_CHILD_NAME].append(rfid_child_doc_json) #end of for

      #print "create_rfid_tag_details_doc checking rfid_doc_json**********",rfid_doc_json

      doc = frappe.new_doc(RFID_DOC_DETAILS_LABEL)
      doc.update(rfid_doc_json)
      doc.save()
      is_created = 1
      return is_created

#packing details api start
@frappe.whitelist()
def fetch_tag_packing_details( rfid_tag ):
	stat = {"pointer": "","pointer_rarb_id":"","pointer_warehouse":"","tag_attached":"","tag_doc_id": "","box_status": "" ,"box_name": "", "box_doc_id" :"","pb_rarb_id":"","pi_rarb_id":""  }
	doc_id = frappe.db.get_value(RFID_DOC_DETAILS_LABEL, {"rfid_tag":rfid_tag},"name")
	rfid_tag_details_doc = frappe.get_doc( RFID_DOC_DETAILS_LABEL,doc_id )
	last_row_idx = 0 	# lastrow
	for roww in getattr(rfid_tag_details_doc,RFID_DOC_DETAILS_CHILD_NAME):
		last_row_idx = last_row_idx +1

	for roww in getattr(rfid_tag_details_doc,RFID_DOC_DETAILS_CHILD_NAME):
		if roww.idx == last_row_idx: #check for packing box/item
			associated_doctype =  roww.pch_rfid_doctype_associated_with
			stat["tag_attached"] = associated_doctype
			stat["tag_doc_id"] = roww.pch_rfid_docid_associated_with

			#pb logic
			if associated_doctype == "Packed Box Custom" :
				stat["pointer"] = "PBOX"
				stat["pointer_rarb_id"] =  frappe.db.get_value(associated_doctype, {"name":roww.pch_rfid_docid_associated_with},"current_rarb_id")
				stat["pointer_warehouse"] =  frappe.db.get_value(associated_doctype, {"name":roww.pch_rfid_docid_associated_with},"current_warehouse")
				stat["box_doc_id"] = roww.pch_rfid_docid_associated_with
				stat["box_name"] = frappe.db.get_value(associated_doctype, {"name":roww.pch_rfid_docid_associated_with},"packing_box")
				stat["box_status"] = frappe.db.get_value(associated_doctype, {"name":roww.pch_rfid_docid_associated_with},"status")
				stat["pb_rarb_id"] = frappe.db.get_value(associated_doctype, {"name":roww.pch_rfid_docid_associated_with},"current_rarb_id")

			#pi logic
			if associated_doctype == "Packed Item Custom" :
				box_id = get_box_id(roww.pch_rfid_docid_associated_with)
				pi_rarb_id =  frappe.db.get_value(associated_doctype, {"name":roww.pch_rfid_docid_associated_with},"current_rarb_id")
				stat["pi_rarb_id"] = pi_rarb_id
				if box_id : #if this packing item  have pb then it will come here
					box_status = frappe.db.get_value("Packed Box Custom", {"name":box_id},"status")
					pi_pb_rarb_id = frappe.db.get_value("Packed Box Custom", {"name":box_id},"current_rarb_id") #pb rarb id where this packing item is placed
					stat["box_status"] = box_status
					stat["box_doc_id"] = box_id
					stat["box_name"] = frappe.db.get_value("Packed Box Custom", {"name":box_id},"packing_box")
					stat["box_status"] = box_status
					stat["pb_rarb_id"] = frappe.db.get_value("Packed Box Custom", {"name":box_id},"current_rarb_id")


					if box_status == "Completed" : #poniter datas will come in these if else loop
						stat["pointer"] = "PBOX"
						stat["pointer_rarb_id"] = pi_pb_rarb_id
						stat["pointer_warehouse"] = frappe.db.get_value("Packed Box Custom", {"name":box_id},"current_warehouse")
					else:
						stat["pointer"] = "PITEM"
						stat["pointer_rarb_id"] = pi_rarb_id
						stat["pointer_warehouse"] = frappe.db.get_value(associated_doctype, {"name":roww.pch_rfid_docid_associated_with},"current_warehouse")

				else: #if this packing item does not have pb then it will come here
					stat["pointer"] = "PITEM"
					stat["pointer_rarb_id"] = pi_rarb_id
					stat["pointer_warehouse"] = frappe.db.get_value(associated_doctype, {"name":roww.pch_rfid_docid_associated_with},"current_warehouse")

					stat["box_status"] = "No PBOX"
					stat["box_doc_id"] = "No PBOX"
					stat["box_name"] = "No PBOX"
					stat["box_status"] = "No PBOX"
					stat["pb_rarb_id"] = "No PBOX"

	return stat

def get_box_id(pitem_id):
	box_id =frappe.db.sql("""select parent,packed_item from `tabPacked Box Breif Details Child` where packed_item= %s """, (pitem_id),as_dict=1)
	print("box_id",box_id)
	return box_id[0]["parent"] if box_id else None


@frappe.whitelist()
def test_pd_from_android():
	return "yes comming"

@frappe.whitelist()
def fetch_si_pipb_details(doc_id):
	doc_total_items_pi_pb_json={}
	#sales invoice item dic (each tems pi and pb details are stored)
	# {si_item : {pi : [],pb : []}}
	si_stat = {"isValid":False,"pb_needed":"","pb_completed":"", "pb_par_completed_qty":"", "pb_pending": "", "pi_needed":"", "pi_completed":"", "pi_par_completed":"", "pi_pending": ""}
	doctype = "Sales Invoice"

	doctype_data = frappe.get_doc(doctype, doc_id)
	si_stat["isValid"] = True if  doctype_data else False
	if si_stat["isValid"] == False :
		return si_stat


	#doc_total_items_pi_pb_json = get_doc_total_items_pi_pb_json(doctype,doc_id)

	dpi_id  = frappe.db.get_value("Detailed Packing Info", {"voucher_no":doc_id},"name")
	dpi_doc = frappe.get_doc("Detailed Packing Info", dpi_id)

	#completed,pi partial and pending calculation
	pi_completed_qty = 0
	pi_pending_qty = 0
	pi_needed = 0

	for dpi_pi_row in dpi_doc.packing_details_review:
		pi_needed = pi_needed + dpi_pi_row.qty
		pi_id =  dpi_pi_row.packing_id
		if pi_id :
			pi_completed_qty = pi_completed_qty + dpi_pi_row.qty
		else:
			pi_pending_qty = pi_pending_qty + dpi_pi_row.qty

	si_stat["pi_completed"] =  pi_completed_qty
	si_stat["pi_pending"] =  pi_pending_qty

	#pb_partial and pending calculation
	pb_completed_qty = 0
	pb_pending_qty = 0
	pb_par_completed_qty = 0
	pb_needed = 0

	for dpi_box_row in dpi_doc.detailed_packing_box:
		pb_needed = pb_needed + 1
		packing_box_id =  dpi_box_row.packing_box_id
		if packing_box_id:
			pbc_doc_status = frappe.db.get_value("Packed Box Custom", {"name":packing_box_id},"status")
			if pbc_doc_status == "Completed" :
				pb_completed_qty = pb_completed_qty +1
			elif pbc_doc_status == "Partially Completed":
				pb_par_completed_qty = pb_par_completed_qty +1
		else:
			pb_pending_qty = pb_pending_qty +1

	si_stat["pb_completed"] =  pb_completed_qty
	si_stat["pb_par_completed"] =  pb_par_completed_qty
	si_stat["pb_pending"] =  pb_pending_qty
	si_stat["pb_needed"] =  pb_needed
	si_stat["pi_needed"] =  pi_needed

	return  si_stat

@frappe.whitelist()
def get_doc_total_items_pi_pb_json(doctype,doc_id): # {si_item1 :{"pi":[],"pb":[]},si_item2:{"pi":[],"pb":[]} }
	doc_total_items_pi_pb_json_temp = { }
	si_item_dic = get_itemwise_qty(doctype,doc_id)

	for item_code, qty in si_item_dic.items():  #iterate over all sales invoice item table
		doc_item_pi_pb_dic={}
		item_master_doc  = frappe.get_doc("Item", item_code)
		doc_item_pi_pb_dic["packing_item_data"]= get_parent_packing_items_list(item_master_doc,qty)
		doc_item_pi_pb_dic["packing_box_data"]= get_parent_item_box_list(item_master_doc,qty)
		doc_total_items_pi_pb_json_temp.update({item_code : doc_item_pi_pb_dic})

		#pi_total_qty_count_for_si
		for pi_item_dic in get_parent_packing_items_list :
			si_stat["pi_needed"] = si_stat["pi_needed"] +  pi_item_dic["pi_qty_ac_to_doc_item_qty"]

		#pb_total_qty_count_for_sis
		for pb_item_dic in get_parent_item_box_list :
			si_stat["pb_needed"] = si_stat["pb_needed"] +  pb_item_dic["pb_qty_ac_to_doc_item_qty"]



	return doc_total_items_pi_pb_json_temp


def get_parent_packing_items_list(item_master_doc,qty):
	#packing item collection data
	parent_packing_items_list=[]
	for child_item in item_master_doc.packing_item_configuration :
		child_item_details={}
		child_item_details["packing_item"] = child_item.packing_item
		child_item_details["pi_qty"] = child_item.qty
		child_item_details["pi_qty_ac_to_doc_item_qty"] = child_item.qty * qty
		child_item_details["packing_item_group"] = child_item.packing_item_group
		parent_packing_items_list.append(child_item_details)
	return parent_packing_items_list

def get_parent_item_box_list(item_master_doc,qty):
	#packing box collection data
	parent_item_box_list = []
	for child_item in item_master_doc.packing_box_configuration :
		packing_box_details = {}
		packing_box_details["packing_box_name"] = child_item.packing_box
		packing_box_details["packing_item"] = child_item.packing_item
		packing_box_details["pb_qty"] = child_item.qty
		child_item_details["pb_qty_ac_to_doc_item_qty"] = child_item.qty * qty
		parent_item_box_list.append(packing_box_details)
	return parent_item_box_list

@frappe.whitelist()
def get_itemwise_qty(doctype,doc_id):
	itemwise_qty_dic = { }
	itemwise_qty_list = frappe.db.sql("""select item_code,qty from `tabSales Invoice Item` where parent= %s """, (doc_id),as_dict=1)
	for itemwise_qty_li in itemwise_qty_list:
		itemwise_qty_dic.update({itemwise_qty_li["item_code"] : itemwise_qty_li["qty"]})
	return itemwise_qty_dic

	#print "itemwise_qty_dic",itemwise_qty_dic
