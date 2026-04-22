# SAT Practice Test 4 — Math Module 2 Incorrect Answer Review

Compared the uploaded PDF questions against the proposed answers in the markdown file.

## Questions that appear to be answered incorrectly

| Question | Proposed answer | Correct answer | Main issue |
|---|---:|---:|---|
| 16 | D) 139 | C) 41 | `z` was treated as equal to `x`, but `z` is supplementary to `x` |
| 20 | `24/51` (or `8/17`) | `15/17` | Used `cos(K)` instead of `cos(L)` |

---

## Q16

**Correct answer: C) 41**

Given:

- $x = 6k + 13$
- $y = 8k - 29$
- lines \(m\) and \(n\) are parallel

At the top intersection, **\(x\)** and **\(y\)** are **vertical angles**, so they are equal:

$6k + 13 = 8k - 29$
$42 = 2k$
$k = 21$

Now find \(x\):


$x = 6(21) + 13 = 126 + 13 = 139$

But the question asks for $z$, not $x$.

Angle $z$ is **same-side interior** with $y$, so they are supplementary:


$z + y = 180$
Since $(y = x = 139)$:
$z = 180 - 139 = 41$

So the correct answer is:

$$41$$



> [!note] Question Type: Parallel lines and angle relationships
> Use the angle relationships in the right order: first identify **vertical angles** to solve for the variable, then use **same-side interior angles** (or a supplementary pair) to get the requested angle.

---

## Q20

**Correct answer:** $\dfrac{15}{17}$

**Given:**
- In triangle $JKL$, angle $J$ is a right angle
- $\cos(K) = \dfrac{24}{51}$

That means, relative to angle $K$:

$$\cos(K) = \frac{\text{adjacent}}{\text{hypotenuse}} = \frac{24}{51}$$

So one leg is $24$ and the hypotenuse is $51$.

Find the other leg with the Pythagorean theorem:

$$\sqrt{51^2 - 24^2} = \sqrt{2601 - 576} = \sqrt{2025} = 45$$

Now evaluate $\cos(L)$. Since $L$ is the other acute angle, the leg adjacent to $L$ is $45$:

$$\cos(L) = \frac{45}{51} = \frac{15}{17}$$

So the correct answer is:

$$\boxed{\frac{15}{17}}$$

> [!warning] Why the proposed answer is wrong
> The proposed solution wrote $\dfrac{24}{51}$, which is $\cos(K)$, not $\cos(L)$. In a right triangle, the two acute angles are complementary, so:
> $$\cos(L) = \sin(K)$$
> And:
> $$\sin(K) = \frac{45}{51} = \frac{15}{17}$$

> [!note] Question Type: Right-triangle trigonometry
> When two acute angles are complementary, one angle’s cosine equals the other angle’s sine. If the question switches from \(K\) to \(L\), make sure you also switch which side is adjacent.

---

## Final check

All other answers in the uploaded markdown file appear to match the PDF questions.
