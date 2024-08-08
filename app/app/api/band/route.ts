import { Album, Artist } from '@/lib/types';
import { faker } from '@faker-js/faker';

const capitalizeFirstLetter = (value: string) => {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export async function GET(req: Request) {
  const albums: Album[] = [...new Array(faker.number.int({ min: 1, max: 5}))].map((_, index) => {
    return {
      name: faker.word.words({ count: { min: 1, max: 5 }}),
      artist: {
        name: capitalizeFirstLetter(faker.word.noun(100)),
        status: "active"
      } as Artist,
      year: faker.number.int({ min: 1982, max: 2024 }),
      label: capitalizeFirstLetter(faker.word.noun(100)) + "Records",
      rating: faker.number.int({ min: 0, max: 100 }),
      reviewCount: faker.number.int({ min: 0, max: 100 }),
      songs: []
    }
  })

  return Response.json({ albums });

}