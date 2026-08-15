A job folder on the Jobs screen — carries its own next action and progress, so the grid answers "which job needs me".

```jsx
<JobCard city="MASON CITY" address="4151 4th St SW - 2026 Tax" meta="18 photos · Tax appeal"
  next={{ label: "Caption 18 photos and build the photo pages", tone: "do" }}
  ready={9} total={16} onClick={open} />
```

Grid is `.rrf-cards` (auto-fill, min 250px); pair with `<NewJobCard />` as the last cell. The next line is one sentence naming the action, never a status word — "Waiting on the rent roll" (tone `waiting`) rather than "Blocked".
