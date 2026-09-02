# COMI syntax and automation patterns

Use this page for the OPERA command language (COMI) in the local 2025 SP1 corpus. It covers language-level syntax that is shared broadly across OPERA workflows. Verify every solver/modeller/post-processor command and parameter against the matching installed release: the converted Markdown contains occasional OCR/transcoding damage.

## Contents

1. [Safe writing rules](#safe-writing-rules)
2. [Values and expressions](#values-and-expressions)
3. [Variables and strings](#variables-and-strings)
4. [Text construction](#text-construction)
5. [Conditions and loops](#conditions-and-loops)
6. [Command files and diagnostics](#command-files-and-diagnostics)
7. [File I/O and tabular output](#file-io-and-tabular-output)
8. [External programs and batch jobs](#external-programs-and-batch-jobs)
9. [Transient control and Python](#transient-control-and-python)
10. [Project architecture](#project-architecture)

## Safe writing rules

- Start built-in commands with `$`. Use full command and parameter names in maintained scripts; although some OPERA values can be abbreviated, abbreviations make scripts fragile and difficult to review.
- Treat command parameter order as significant when positional values are used. Prefer named parameters where the selected command supports them.
- Use `=` for named assignment, e.g. `COMPONENT=...`; do not put spaces inside numeric/logical expressions.
- Use a vertical bar `|` only to join intentionally independent commands. Commands on the line are processed before a newly opened `$COMINPUT` file begins execution.
- Begin a whole-line comment with `/` (after optional leading spaces). With the default `commentstyle=line`, `/` comments the *entire line*, including every command after a `|`.
- Quote strings containing spaces or commas with single quotes. Build dynamically quoted paths with `%QUOTE(...)`, not manual quote concatenation.
- Put all destructive output (`OVERWRITE`, `$OS` deletion, generated database paths) under a case-local output folder. Add a path/overwrite check before running it.

```text
/ Good: a complete comment line
$CONSTANT #gap_mm 12.5
$PARAMETER #gap_m #gap_mm/1000

/ Both commands execute before child.comi begins.
$COMINPUT child.comi | $CONSTANT #case 3
```

## Values and expressions

### Numeric, character, Boolean and list values

| Value | Rule / example |
| --- | --- |
| Numeric | Use integer/fixed/scientific notation, including `3E5`, `-5.789E+04`, or `2.305983743795D5`. |
| Character / filename | Use the complete keyword in maintained scripts. Quote text containing spaces or commas: `'Case 001'`. |
| Boolean | Use `YES`/`NO`, or `+PARAMETER`/`-PARAMETER`. Use `!PARAMETER` only when intentionally toggling a known Boolean state. |
| List | Reset with `PARAMETER=`; set first item with `PARAMETER=value1`; append with `PARAMETER+=value2`. |

Use paths with spaces only as a single quoted value. In the corpus, `VFDIR` is available as an OPERA installation-folder environment variable; `$ENV(...)` can query OS variables in a portable command file.

### Numeric and logical expressions

Expressions accept user variables, system variables, selected command parameters, functions and parentheses. Parameter names used *inside* expressions must be written in full. Do not include spaces.

| Category | Operators / examples |
| --- | --- |
| Arithmetic | unary `+`/`-`, power `**` or `^`, `*`, `/`, `+`, `-` |
| Logic | `!`, `<`, `<=`, `>`, `>=`, `==`, `!=`, `&&`, `||` |
| Comparisons in control commands | `EQ`, `NE`, `LE`, `LT`, `GE`, `GT` |
| Common functions | `ABS`, `MIN`, `MAX`, `MOD`, `NINT`, `SQRT`, `EXP`, `LOG`, `SIN`, `COS`, `ATAN2`, `VMOD2`, `VMOD3` |

Use semicolons between multiple arguments in numeric functions, for example `MAX(ABS(#x1);ABS(#x2))` and `ATAN2(Y;X)`. `SIN/COS/...` use radians; the `...D` variants such as `SIND`, `COSD`, and `ATAN2D` use degrees.

Avoid direct equality for calculated floating-point values. Write a tolerance test instead:

```text
$IF ABS(#computed-#expected)<1E-8
  / Accept result.
$END IF
```

COMI evaluates a logical value as true when its nearest integer is non-zero. Parenthesize mixed arithmetic and logic rather than relying on precedence.

## Variables and strings

### Numeric variables

Numerical user-variable names begin with `#`, are case-insensitive, and can include letters, digits, `_`, `[]`, `#`, and `$` after the leading `#`. Use one role per variable type:

| Form | Meaning | Appropriate use |
| --- | --- | --- |
| `$CONSTANT #x value 'description'` | Evaluate once; retain the numeric value | Inputs, loop-independent derived values, tolerance limits |
| `$PARAMETER #x expression 'description'` | Retain expression; re-evaluate whenever referenced | Quantities that should track changing variables/field system values |
| `$MODELDIMENSION #x value` | Protected parametric model dimension | Dimensions intended for optimization/command-line setup |
| `$EQUATION #x expression` | Solve equation when referenced | Specialized implicit material/model relationships |
| `$SYSVAR name value` | Define a system variable name for expressions | Only when a solver/model workflow requires a normally absent system variable |

Short forms are supported by the reference manual:

```text
#radius=70
#area:=PI*#radius^2
```

The first is a constant; the second is a re-evaluated parameter. Prefer the full form in reusable scripts because its intent is explicit.

Use `##name` for a scoped temporary. Its scope is the control block in which it is first defined, and it disappears when that block ends. Do not let an unscoped `$PARAMETER` depend on a scoped variable.

### String variables

Define a string with `$STRING name value description`; recover it with `&name&` on an input line. String names begin with a letter and are case-insensitive. Use `%QUOTE` whenever an expanded string becomes a single path/text argument.

```text
$STRING case_id 'gap_12p5mm'
$STRING results_folder 'results\&case_id&'
$STRING table_file %QUOTE<&results_folder&\summary.txt>
```

Useful pre-defined strings in the local reference include `PROJECTFOLDER`, `WORKINGFOLDER`, `VERSION`, `VFEXAMPLESDIR`, `COMIBASENAME`, and `COMIPATH`. `YESORNO=YES` can answer file-overwrite/end prompts during command-file execution; never set it globally in a script that has not proved its output paths are safe.

## Text construction

Text functions begin with `%`. Use parentheses with comma-separated arguments, or use matching `{}`, `[]`, or `<>` argument delimiters. The non-parenthesis forms are especially useful when strings contain commas or nested parentheses.

| Function | Use |
| --- | --- |
| `%COMPARE(a,b[,CS])` | Compare strings; returns `-1`, `0`, or `1`; default comparison is case-insensitive |
| `%EXISTVAR(#x)`, `%EXISTSTR(name)` | Guard optional variables/strings |
| `%ENV(name)` | Read an OS/OPERA environment variable |
| `%INT`, `%NINT`, `%REAL` | Convert an expression to text; use for indexed names or expression-to-character parameters |
| `%QUOTE(text)` | Create one correctly quoted command argument |
| `%FILEBASENAME`, `%FILEPATH`, `%FILECOUNT` | Build/check filenames |
| `%FIND`, `%SUBSTR`, `%REPLACE`, `%STRLENGTH` | Parse or transform controlled strings |
| `%EXPR(variable)` | Reuse/extend an existing expression |

Example: safely create indexed output names and avoid redefining a user's supplied parameter.

```text
$IF !%EXISTVAR(#radius)
  $CONSTANT #radius 70 'Sampling radius [mm]'
$END IF
$DO #i 1 3
  $STRING output_name %QUOTE<result_%INT(#i,3).txt>
  / Use &output_name& only in a verified file-writing command.
$END DO
```

## Conditions and loops

### Condition blocks

Use `$IF`, `$ELIF`, `$ELSE`, `$END IF`. A condition can be a numeric expression or `left operator right` using `EQ/NE/LE/LT/GE/GT`.

```text
$IF #current_A GT 0
  / Positive excitation branch.
$ELIF #current_A LT 0
  / Reversed excitation branch.
$ELSE
  / De-energized branch.
$END IF
```

Use `%COMPARE(&string&,expected) EQ 0` for exact string-choice logic. To write one script usable in several OPERA contexts, test the documented `PROGRAM` value rather than guessing the active processor.

### Loops

| Form | Syntax | Notes |
| --- | --- | --- |
| Numeric sequence | `$DO #i start final [increment]` ... `$END DO` | Evaluate start/final/increment before the first pass; default increment is 1; do not redefine index inside the loop. |
| Explicit values | `$FOR #x ex1 ex2 ... ex9` ... `$END FOR` | Iterate one user variable through up to nine expressions. |
| Condition | `$WHILE condition` ... `$END WHILE` | Add an explicit counter/exit condition to prevent accidental infinite loops. |
| Skip / break | `$CYCLE [blocks]`; `$EXIT [blocks]` | Default is current loop/block; a value greater than 1 targets an outer level. |

Use an error-aware file-reading loop only when the file length is unknown:

```text
$ERRORHANDLER NO
$WHILE 1
  $READ #input #x #y -PRINT
  $BREAKERROR
  / Process a successfully read row.
$END WHILE
$ERRORHANDLER YES
```

Place `$BREAKERROR` immediately after the potentially failing `$READ`. Restore `$ERRORHANDLER YES` before any normal solving/post-processing commands; otherwise stored command execution can continue after an unrelated error.

## Command files and diagnostics

### Include and relative paths

Use `$COMINPUT filename [mode] [commentstyle]`. Omit `.comi` only when that extension is intended. A relative include inside `parent.comi` is resolved relative to `parent.comi`, not implicitly to the project root. This enables portable script modules:

```text
/ model-build.comi
$COMINPUT model-dimensions.comi CONTINUOUS LINE
$COMINPUT geometry.comi CONTINUOUS LINE
$COMINPUT materials.comi CONTINUOUS LINE
```

`$COMINPUT` can also run a `.py` file, but use the documented `$PYTHON FILE=...` form for solver-linked Python and verify the exact release syntax.

Use `CONTINUOUS` while developing to retain diagnostic output. Use `OFF` only for a proven non-interactive production path. `$PAUSE seconds` is suitable for interactive demos, not unattended automation. Use `$ABORTCOMI` only after writing a clear diagnostic/output state.

### Check failures deliberately

| Check | Pattern |
| --- | --- |
| File/folder exists | `$EXIST filename`, then test `FILEEXISTS` (and `FILETYPE` when needed) |
| Optional file count | `%FILECOUNT(path)` or `%FILECOUNT(folder,filter)` |
| External executable exit | `$EXEC ... +WAIT`, then test `EXECEXITCODE` |
| Current data context | inspect documented `PROGRAM`, `WORKINGFOLDER`, and `COMIPATH` |

Write compact provenance to the dialogue/result stream: case ID, parameter values, source database, reference radius, output filename and program stage. Do not suppress an error merely to continue a sweep.

## File I/O and tabular output

Use logical stream numbers 1–50. `$OPEN 0 file authority` asks OPERA to select the next free stream and stores it in `OPENSTREAM`.

| Command | Form | Purpose |
| --- | --- | --- |
| Open | `$OPEN stream file READ|WRITE|OVERWRITE|APPEND [±REDIRECT] [±USERVARIABLES]` | Open a case-local file; `+USERVARIABLES` writes restore-able variable commands |
| Close | `$CLOSE stream` | Release a stream |
| Read | `$READ stream var1 var2 ... [±PRINT]` | Read one line into up to 99 variables |
| Write | `$WRITE stream data1 data2 ... [±OUTPUT]` | Write up to 99 data items |
| Format | `$FORMAT ...` then `$ASSIGN ...` | Define deterministic text/numeric output columns |
| Reposition | `$BACKSPACE stream records` | Backspace/rewind a supported stream |

Build a table with explicit formats rather than scraping human-readable solver text:

```text
$OPEN 0 results.txt OVERWRITE
$CONSTANT #out OPENSTREAM
$FORMAT 1 STRING 1 STRING=' '
$FORMAT 2 EXPONENTIAL 0
$ASSIGN 2 1 2 1 2
/ After a verified field/integral command has set its result variables:
$WRITE #out #radius 0 #integral_field 0 #error_metric
$CLOSE #out
```

Use `-OUTPUT` for intermediate `$WRITE` fragments and `+OUTPUT` for the final fragment of one line. Do not share output streams between concurrent external cases.

## External programs and batch jobs

Prefer `$EXEC` to launch a known executable. It accepts a program, a list of arguments and `+WAIT`/`-WAIT`. Build arguments one at a time; with `+WAIT`, inspect `EXECEXITCODE` before continuing.

```text
$EXEC 'path\to\program.exe' ARGUMENTS='first argument'
$EXEC 'path\to\program.exe' ARGUMENTS+='second argument' +WAIT
$IF EXECEXITCODE NE 0
  / Record failure and stop this case by a verified project policy.
$END IF
```

Use `$OS` only for tightly scoped operational tasks. It executes through the operating system and can list, copy, rename or delete files; quote Windows filenames with spaces using double quotes *inside* the OS command. Use `$CD` to change OPERA's working directory—`$OS cd ...` changes only a spawned subprocess and has no lasting effect.

For parameter studies, prefer an external Python launcher that creates one working folder/database/log set per case. Let COMI build and extract each single case; do not use one shared database as mutable sweep state.

## Transient control and Python

Keep the following mechanisms distinct:

| Mechanism | Use |
| --- | --- |
| `solver.comi` | Execute once when the 3D solver launches; import case-local Python and register callbacks. Keep it beside the model/Python file when the selected workflow requires that discovery convention. |
| `control_<solver>.comi` | Solver-specific time-step control. The user guide documents names such as `control_carmen.comi` for Motional EM and `control_elektratr.comi` for Transient EM; use the exact solver-specific name only after checking the installed example. |
| `$PYTHON FILE=...` / `$PYTHON COMMAND=...` | Load Python or execute a Python statement under OPERA's command language. Validate command spelling and callback identifiers in the installed manual/example. |
| `$EXEC ... +WAIT` | Launch an external program synchronously; use only when the coupling/output contract is explicit. |

For adaptive transient stepping, the local Motional EM guide says to apply switch-state changes at **END** of a time step and time-step method/value changes at **START**. Preserve this timing distinction in `control_*.comi` scripts.

## Project architecture

| File | Responsibility |
| --- | --- |
| `model-dimensions.comi` | Constants/parameters, units, case ID and validation guards |
| `model-build.comi` | Geometry/import, labels, material/excitation assignment, mesh, analysis database |
| `solver.comi` | One-time Python initialization and registered hooks, if required |
| `control_<solver>.comi` | Transient drive/motion/circuit state, only for its compatible solver |
| `post-process.comi` | Field maps, line/surface integrals, harmonics and explicit results table |
| `run_cases.py` | Case-folder creation, input rendering, bounded launch, log capture, result collation |

Keep scripts idempotent for a *new* case directory. Make all generated file names include a stable case identifier. Before scaling, run a nominal scripted case and compare its key result, sign, units, symmetry and solver log with a trusted manual/GUI baseline.
