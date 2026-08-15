A folder's state on the job screen — what has arrived, what is still missing.

```jsx
<FolderCard folder="Subject Information" count={6} has={["the engagement letter", "the deed"]} needs={["the assessor PRC"]} />
```

Pass plain noun phrases; the component writes the sentence and the Oxford comma. Green = has, amber = needs; never red.
