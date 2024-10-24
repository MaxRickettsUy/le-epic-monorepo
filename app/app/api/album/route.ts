import { Album } from '@/lib/types';
import { faker } from '@faker-js/faker';

const capitalizeFirstLetter = (value: string) => {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export async function POST(req: Request) {
  const data = await req.json();

  const album: Album = {
      name: data.name,
      bandName: data.bandName,
      year: faker.number.int({ min: 1982, max: 2024 }),
      label: capitalizeFirstLetter(faker.word.noun(100)) + "Records",
      rating: faker.number.int({ min: 0, max: 100 }),
      reviewCount: faker.number.int({ min: 0, max: 100 }),
      songs: [...new Array(faker.number.int({ min: 3, max: 12}))].map((_, index) => {
        return {
          name: faker.word.words({ count: { min: 1, max: 3} }),
          length: "2:30"
        }
      })
  }

  return Response.json(album);

}