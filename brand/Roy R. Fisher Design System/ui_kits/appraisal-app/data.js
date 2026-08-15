/* Synthetic job data. Addresses and clients are invented; no real client,
   address, or valuation appears anywhere in this kit. */
window.DEMO = {
  jobs: [
    { name: "MASON CITY_4151 4th St SW - 2026 Tax", photos: 18, engagement: "Tax appeal", type: "retail",
      next: { label: "Caption 18 photos and build the photo pages", tone: "do" }, ready: 9, total: 16 },
    { name: "DAVENPORT_5515 Utica Ridge - 2026", photos: 9, engagement: "Full appraisal", type: "office",
      next: { label: "Choose the sections this report needs", tone: "do" }, ready: 0, total: 19 },
    { name: "BETTENDORF_1240 Middle Road - 2026", photos: 0, engagement: "Restricted short form", type: "special purpose",
      next: { label: "Waiting on the rent roll and the owner income history", tone: "waiting" }, ready: 7, total: 11 },
    { name: "IOWA COUNTY_2172 M Avenue - 2025 Tax", photos: 24, engagement: "Tax appeal", type: "industrial",
      next: { label: "Nothing pending. Every section has what it needs.", tone: "done" }, ready: 16, total: 16 },
  ],
  folders: [
    { folder: "Subject Information", count: 6, here: ["the engagement letter", "the deed", "the assessment notice"], needs: ["the assessor PRC"] },
    { folder: "Photos", count: 18, here: ["inspection photos"], needs: [] },
    { folder: "Maps", count: 3, here: ["the plat map", "the flood map"], needs: ["a zoning snip", "a building sketch"] },
    { folder: "Demographic", count: 4, here: ["the ESRI market profile", "a CoStar submarket report"], needs: [] },
    { folder: "Comps", count: 7, here: ["five improved sales"], needs: ["the comp location map"] },
    { folder: "Financials", count: 0, here: [], needs: ["the owner income and expense history", "the rent roll"] },
    { folder: "Legal", count: 0, here: [], needs: [] },
  ],
  sections: [
    "Title Page", "Letter of Transmittal", "Statement of the Appraisal Problem",
    "Salient Facts Summary", "Subject Photographs", "Neighborhood Description",
    "Site Analysis", "Description of Improvements", "Market Overview",
    "Highest and Best Use", "Cost Approach", "Sales Comparison Approach",
    "Income Approach", "Correlation and Value Estimate", "Certification",
    "Contingent and Limiting Conditions", "Addenda",
  ],

  /* The report, with where each section stands. "needs" is the only place in the
     app that says something is not ready — never the worklist. */
  reportRows: [
    { name: "Title Page" },
    { name: "Letter of Transmittal" },
    { name: "Statement of the Appraisal Problem" },
    { name: "Salient Facts Summary" },
    { name: "Subject Photographs", live: true, has: "18 photos in the folder" },
    { name: "Neighborhood Description" },
    { name: "Site Analysis", needs: "waiting on the assessor PRC and a zoning snip" },
    { name: "Description of Improvements", needs: "waiting on the assessor PRC and the building sketch" },
    { name: "Market Overview", has: "the ESRI profile and CoStar report are in" },
    { name: "Highest and Best Use" },
    { name: "Cost Approach", note: "not in scope for this appeal" },
    { name: "Sales Comparison Approach", needs: "waiting on the comp location map" },
    { name: "Income Approach", needs: "waiting on the rent roll and the expense history" },
    { name: "Correlation and Value Estimate" },
    { name: "Certification" },
    { name: "Contingent and Limiting Conditions" },
  ],

  /* Every gap is a task, and every task names the sections that wait on it and
     the folder it belongs in. Ordered by what he can do without waiting. */
  tasks: [
    { icon: "image", name: "Caption the photos and build the photo pages", chip: "Open", go: "photos",
      why: "Subject Photographs is the only section that builds so far. 18 photos are in the folder." },
    { icon: "file-text", name: "Check the section list for this tax appeal", chip: "Open", go: "sections",
      why: "16 sections came from the engagement matrix. Nothing is confirmed yet." },
    { icon: "folder", name: "Add the assessor PRC", chip: "Open folder",
      why: "Site Analysis and Description of Improvements are both waiting on it. Goes in Subject Information." },
    { icon: "folder", name: "Add a zoning snip and the building sketch", chip: "Open folder",
      why: "Site Analysis cites the zoning district; Improvements needs the sketch. Both go in Maps." },
    { icon: "folder", name: "Add the comp location map", chip: "Open folder",
      why: "Sales Comparison Approach is waiting on it. Goes in Comps." },
    { icon: "folder", name: "Add the rent roll and the expense history", chip: "Open folder",
      why: "The Income Approach cannot start without them. Both go in Financials." },
  ],
  arrived: [
    { name: "Engagement letter, deed and assessment notice are in", why: "Subject Information · 6 files" },
    { name: "ESRI market profile and CoStar submarket report are in", why: "Demographic · 4 files" },
    { name: "Five improved sales are in", why: "Comps · 7 files" },
    { name: "Plat map and flood map are in", why: "Maps · 3 files" },
    { name: "18 inspection photos are in", why: "Photos · 18 files" },
  ],

  /* Nine folders for a tax appeal, eleven for a full appraisal. */
  folderCounts: { "Tax appeal": 9, "Full appraisal": 11, "Restricted short form": 7, "Rent study": 7, "Right of way": 9 },
  photos: [
    { file: "IMG_0412.jpg", src: "../../assets/photography/commercial-real-estate.jpg", caption: "West elevation of the subject, viewed from 4th Street SW toward the loading area" },
    { file: "IMG_0413.jpg", src: "../../assets/photography/cedar-rapids.jpg", caption: "Street frontage and parking, looking north" },
    { file: "IMG_0414.jpg", src: "../../assets/photography/iowa-city.jpg", caption: "" },
    { file: "IMG_0415.jpg", src: "../../assets/photography/commercial-real-estate.jpg", caption: "Rear service drive and dock" },
    { file: "IMG_0416.jpg", src: "../../assets/photography/cedar-rapids.jpg", caption: "" },
    { file: "IMG_0417.jpg", src: "../../assets/photography/iowa-city.jpg", caption: "Interior, sales floor looking east" },
  ],
  captionStyles: [
    { key: "view", label: "What it shows", sample: "West elevation and loading area" },
    { key: "facing", label: "Which way it faces", sample: "Looking east from 4th Street SW" },
  ],
  engagements: ["Full appraisal", "Tax appeal", "Restricted short form", "Rent study", "Right of way"],
  types: ["retail", "office", "industrial", "multi-family", "special purpose"],
};
