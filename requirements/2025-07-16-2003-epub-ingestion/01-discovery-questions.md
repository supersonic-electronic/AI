# Discovery Questions

## Q1: Should the EPUB extractor handle both text content and embedded mathematical formulas like the existing PDF extractor?
**Default if unknown:** Yes (the system has sophisticated mathematical content detection and the EPUB format commonly contains technical documents with formulas)

## Q2: Should the EPUB extractor preserve chapter structure and metadata (title, author, table of contents) in the extracted output?
**Default if unknown:** Yes (EPUB files have rich structural metadata that would be valuable for document organization and reference)

## Q3: Should the EPUB extractor handle embedded images and media content within EPUB files?
**Default if unknown:** No (based on the existing PDF extractor configuration showing `include_images: false`, the system appears focused on text extraction)

## Q4: Should the EPUB extractor support encrypted/DRM-protected EPUB files?
**Default if unknown:** No (most open academic and technical content uses unprotected EPUBs, and DRM handling adds significant complexity)

## Q5: Should the EPUB extraction process include the same chunking and embedding pipeline as other document formats?
**Default if unknown:** Yes (the system has a consistent processing pipeline with `chunk_size`, `chunk_overlap`, and embedding generation for all document types)