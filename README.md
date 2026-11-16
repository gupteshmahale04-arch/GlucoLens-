# GlucoLens: Explainable Postprandial Blood Glucose Prediction

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Paper arXiv](https://img.shields.io/badge/arXiv-2503.03935-b31b1b.svg)](https://arxiv.org/abs/2503.03935)

</div>

**GlucoLens** is an explainable machine learning framework designed to predict postprandial blood glucose dynamics (such as hyperglycemia risks, Positive Area Under the Curve - PAUC, and Maximum Postprandial Blood Glucose - MaxPBG) using daily diet, continuous glucose monitoring (CGM) streams, and physical activity logs.

---

## 📖 Overview
Postprandial hyperglycemia—the sharp spike in blood glucose following meals—is a primary precursor to type 2 diabetes and metabolic dysfunction. GlucoLens bridges the gap between raw biometric sensing and actionable health insights by combining machine learning regression models with **counterfactual explanations** (via DiCE). This helps individuals understand not just *if* they are at risk of a glucose spike, but *what minimal changes* in diet or physical activity can prevent it.

---

## 🧬 System Architecture & Data Pipeline
The GlucoLens body sensor network and data pipeline process multi-modal inputs:
1. **Continuous Glucose Monitors (CGMs):** Captures real-time blood glucose trends (averaged over 15-minute windows).
2. **Food & Activity Logs:** Records nutritional details (macronutrients, net carbs, fat, protein, fiber) and work/movement habits.
3. **Glycemic Load (GL) Calculation:** 
   $$\text{GL} = 19.27 + (0.39 \times \text{net carbs}) - (0.21 \times \text{fat}) - (0.01 \times \text{protein}^2) - (0.01 \times \text{fiber}^2)$$
4. **Machine Learning Core:** Evaluates multiple feature sets across models like Random Forest (RF), Ridge Regression, and Multilayer Perceptrons (MLP).
5. **Explainability Layer:** Generates personalized, counterfactual recommendations to alter risky glucose trajectories.

---

## 🚀 Key Features
- **Accurate Blood Glucose Metrics:** Predicts PAUC, $\Delta\text{PAUC}$, and MaxPBG with high performance (Random Forest backend outperforming baseline methods).
- **Explainable AI (XAI):** Implements diverse counterfactual explanations to provide users with achievable dietary and activity modifications.
- **Multimodal Feature Integration:** Flexible feature sets combining sensor streams, self-reported logs, and derived glycemic load metrics.

---

## 🛠️ Installation & Setup

Clone the repository and set up your environment:

```bash
# Clone the repository
git clone https://github.com/gupteshmahale04-arch/GlucoLens-.git
cd GlucoLens-

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 Usage

Instructions for running model training, feature evaluations, and generating explanations:

```python
# Example snippet for model execution and evaluation pipeline
from src.models import train_random_forest
from src.utils import load_processed_data

# Load dataset feature sets
data = load_processed_data('data/processed_features.csv')

# Train and evaluate model
model, metrics = train_random_forest(data)
print(f"Model Performance (NRMSE): {metrics['nrmse']}")
```

---

## 📊 Evaluation Metrics
- **NRMSE:** Normalized Root Mean Squared Error for regression targets.
- **Accuracy:** Hyperglycemia classification tracking.
- **PAUC / MaxPBG:** Postprandial glycemic excursion measurements.

---

## 🤝 Contributing
Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request.

1. Fork the Project (`https://github.com/gupteshmahale04-arch/GlucoLens-/fork`)
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git origin push feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 Citation
If you use GlucoLens in your research, please cite the corresponding paper:
```bibtex
@article{glucolens2025,
  title={GlucoLens: Explainable Postprandial Blood Glucose Prediction from Diet and Physical Activity},
  author={Mamun, Abdullah and Arefeen, A. and Racette, S. B. and Ghasemzadeh, H.},
  journal={arXiv preprint arXiv:2503.03935},
  year={2025}
}
```

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
