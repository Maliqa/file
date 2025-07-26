import streamlit as st
import pandas as pd
from collections import Counter

st.title("🌀 Prediksi 4D Tesla 369 (99 Angka)")
st.write("""
**Cara Pakai:**
1. Masukkan 4 digit (0000-9999)  
2. Dapatkan 99 prediksi 4D  
3. Analisis digit paling sering muncul
""")

# Input 4 digit dengan validasi
input_4d = st.text_input("Masukkan 4 digit (0000-9999):", max_chars=4)

def generate_4d_tesla(base_num, count=99):  # Ubah count menjadi 99
    seed = int(base_num)
    multipliers = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48]
    return [
        str((seed + (i+1)*multipliers[i%len(multipliers)]*369) % 10000).zfill(4)
        for i in range(count)
    ]

def analyze_digits(predictions):
    all_digits = [d for num in predictions for d in num]
    freq = Counter(all_digits)
    return pd.DataFrame({
        "Digit": [str(k) for k in freq.keys()],
        "Frekuensi": [int(v) for v in freq.values()]
    }).sort_values("Frekuensi", ascending=False)

if st.button("⚡ Generate 99 Prediksi"):
    if not input_4d.isdigit() or len(input_4d) != 4:
        st.error("Input harus 4 digit (0000-9999)!")
    else:
        with st.spinner("Menghitung 99 pola kosmik..."):
            predictions = generate_4d_tesla(input_4d)
            freq_df = analyze_digits(predictions)
            
            # Tampilkan dalam 2 tab
            tab1, tab2 = st.tabs(["🔢 99 Prediksi 4D", "📊 Analisis Frekuensi"])
            
            with tab1:
                # Tampilkan 99 angka dalam 3 kolom
                cols = st.columns(3)
                for i, num in enumerate(predictions, 1):
                    with cols[i % 3]:
                        st.markdown(f"**{i}.** `{num}`")
                
            with tab2:
                st.dataframe(
                    freq_df,
                    column_config={
                        "Digit": "Digit",
                        "Frekuensi": st.column_config.ProgressColumn(
                            "Frekuensi",
                            format="%d",
                            min_value=0,
                            max_value=int(freq_df["Frekuensi"].max())
                        )
                    },
                    hide_index=True,
                    height=500
                )
                st.bar_chart(freq_df.set_index("Digit"))

st.markdown("---")
st.caption("""
**Formula Tesla 369 4D:**  
`(input + (index+1) × [3,6,9,...48] × 369) mod 10000`  
*99 angka unik dengan pola energi 369*
""")