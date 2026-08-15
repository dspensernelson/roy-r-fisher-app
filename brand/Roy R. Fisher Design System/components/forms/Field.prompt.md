The app's only text input — labelled, with hint and error built in.

```jsx
<Field label="Street address" value={street} onChange={setStreet} placeholder="4151 4th St SW" />
<Field label="Kind of appraisal" options={ENGAGEMENTS} value={eng} onChange={setEng} />
<Field mono label="Paste your key" type="password" value={key} onChange={setKey} />
```

Labels are plain words, not jargon: "Kind of property", not "Property type classification". Grid several with `.rrf-fields`. There is one tone — paper, hairline, 6px, the same object as a row.
