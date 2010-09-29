- Fix a bug in BaseManage_Rename Folder_Rename.action(...) can return None
- repository: Remove content-children-toc from fixed handlers
- sidebar/twitter: Male _update_data more robust is the title is not well formed
- itws: Fix bug when creating new boxes from ws-data view
- repository: Remove obsolete BoxSectionChildrenToc
- do not force contentbar width for tracker add issue (bug 938)
- add new class based on resources tree name, to be able to customize a
  specific section or resource view
  (i.e. #content.our-solutions.product1 -> /our-solutions/product1/;view)
- views: Fix CSS_Edit, add missing database.change_resource call
- sidebar news: use thumbnail instead of download for news preview image (96x96)
