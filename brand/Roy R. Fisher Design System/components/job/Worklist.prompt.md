Groups the job screen's TaskRows under a small uppercase heading.

```jsx
<Worklist title="You can do these now">{tasks}</Worklist>
<Worklist title="Already here">{arrived}</Worklist>
```

The proposal uses two groups and puts things he cannot do yet on the section rows instead — that is a product call, explained in `ui_kits/appraisal-app/PROPOSAL.md`. The component takes any number of groups with any titles.
