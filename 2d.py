import streamlit as st

st.title("Generator Prediksi Togel 2D (39 Output - Fibonacci)")

st.write(
    """
    Masukkan angka 2D terakhir (misal: 23). 
    Prediksi dihasilkan dengan pola Fibonacci probabilitas, 
    hanya menggunakan 2 digit terakhir dari penjumlahan (tidak akan error limit digit).
    """
)

last_result = st.text_input("Angka 2D terakhir:", max_chars=2)
generate = st.button("Buat Prediksi")

def fibonacci_2d(seed, jumlah):
    # Ambil dua digit dari seed, misal '23' jadi 2 dan 3
    angka1 = int(seed[0])
    angka2 = int(seed[1])
    hasil = []
    # Loop sampai dapat jumlah prediksi yang diinginkan
    while len(hasil) < jumlah:
        next_angka = (angka1 + angka2) % 100  # Selalu 2 digit saja
        prediksi = str(next_angka).zfill(2)
        # Hindari duplikat dan angka input
        if prediksi not in hasil and prediksi != seed:
            hasil.append(prediksi)
        angka1, angka2 = angka2, next_angka
    return hasil

if generate:
    if not last_result.isdigit() or len(last_result) != 2:
        st.error("Input harus 2 digit angka (misal: 23)")
    else:
        prediksi_list = fibonacci_2d(last_result, 39)
        st.success("39 Prediksi Angka 2D (Metode Fibonacci):")
        for i, num in enumerate(prediksi_list, 1):
            st.write(f"{i}. {num}")