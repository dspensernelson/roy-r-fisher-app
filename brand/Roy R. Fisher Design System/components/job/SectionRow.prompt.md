A row in the report's section list.

```jsx
<SectionRow num={5} name="Subject Photographs" state="18 photos in the folder" live onClick={openPhotos} />
<SectionRow num={7} name="Site Analysis" stateTone="needs" state="waiting on the assessor PRC and a zoning snip" />
<SectionRow num={9} name="Market Overview" stateTone="has" state="the ESRI profile and CoStar report are in" />
```

The proposal lists every section, including the ones that cannot build, so the list shows the report's real shape, and puts "waiting on…" here rather than in the worklist — see `ui_kits/appraisal-app/PROPOSAL.md` for why. Both are product calls, not brand ones.
